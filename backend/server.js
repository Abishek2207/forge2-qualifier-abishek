"use strict";

const express  = require("express");
const cors     = require("cors");
const cron     = require("node-cron");
const { v4: uuidv4 } = require("uuid");
const fs       = require("fs");
const path     = require("path");

// ─────────────────────────────────────────────────────────────────────────────
// Configuration
// ─────────────────────────────────────────────────────────────────────────────
const PORT      = process.env.PORT || 3000;
const DB_PATH   = path.join(__dirname, "tasks.json");
const START_TIME = Date.now();

// ─────────────────────────────────────────────────────────────────────────────
// Console colour helpers
// ─────────────────────────────────────────────────────────────────────────────
const C = {
  reset:  "\x1b[0m",
  bold:   "\x1b[1m",
  cyan:   "\x1b[36m",
  yellow: "\x1b[33m",
  green:  "\x1b[32m",
  red:    "\x1b[31m",
  dim:    "\x1b[2m",
};

const log = {
  hermes:   (msg) => console.log(`${C.cyan}${C.bold}[HERMES]  ${C.reset} ${msg}`),
  openclaw: (msg) => console.log(`${C.yellow}${C.bold}[OPENCLAW]${C.reset} ${msg}`),
  result:   (msg) => console.log(`${C.green}${C.bold}[RESULT]  ${C.reset} ${msg}`),
  system:   (msg) => console.log(`${C.dim}[SYSTEM]  ${C.reset} ${msg}`),
  error:    (msg) => console.error(`${C.red}${C.bold}[ERROR]   ${C.reset} ${msg}`),
};

// ─────────────────────────────────────────────────────────────────────────────
// File-based Database
// ─────────────────────────────────────────────────────────────────────────────

/**
 * loadTasks()
 * Reads tasks.json from disk.
 * Safe against: file-not-found, empty file, malformed JSON.
 * Always returns an Array.
 */
function loadTasks() {
  try {
    if (!fs.existsSync(DB_PATH)) {
      log.system("tasks.json not found — starting with empty store.");
      return [];
    }

    const raw = fs.readFileSync(DB_PATH, "utf8").trim();
    if (!raw) {
      log.system("tasks.json is empty — starting with empty store.");
      return [];
    }

    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      log.error("tasks.json root is not an array — resetting to [].");
      return [];
    }

    return parsed;
  } catch (err) {
    log.error(`loadTasks failed: ${err.message} — resetting to [].`);
    return [];
  }
}

/**
 * saveTasks(tasks)
 * Writes the task array to tasks.json atomically (write to .tmp then rename).
 * Safe against partial-write corruption.
 */
function saveTasks(tasks) {
  try {
    const tmp = DB_PATH + ".tmp";
    fs.writeFileSync(tmp, JSON.stringify(tasks, null, 2), "utf8");
    fs.renameSync(tmp, DB_PATH);
  } catch (err) {
    log.error(`saveTasks failed: ${err.message}`);
    throw err; // let the caller handle if needed
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Bootstrap in-memory store from disk
// ─────────────────────────────────────────────────────────────────────────────
let tasks = loadTasks();
log.system(`Loaded ${tasks.length} task(s) from disk.`);

// ─────────────────────────────────────────────────────────────────────────────
// Express Application
// ─────────────────────────────────────────────────────────────────────────────
const app = express();

app.use(cors());
app.use(express.json());

// ── Request logger (lightweight) ─────────────────────────────────────────────
app.use((req, _res, next) => {
  console.log(`${C.dim}${new Date().toISOString()}  ${req.method.padEnd(7)} ${req.path}${C.reset}`);
  next();
});

// ─────────────────────────────────────────────────────────────────────────────
// System / Health Endpoints
// ─────────────────────────────────────────────────────────────────────────────

// GET /  — root health check (Render pings this)
app.get("/", (_req, res) => {
  res.json({
    system:  "AI Kanban Agent System",
    version: "2.0.0",
    status:  "online",
    agents: {
      hermes:   { role: "planner",  status: "active" },
      openclaw: { role: "executor", status: "active" },
    },
    taskCount: tasks.length,
    uptime:    `${Math.floor((Date.now() - START_TIME) / 1000)}s`,
    timestamp: new Date().toISOString(),
  });
});

// GET /health  — uptime + basic liveness
app.get("/health", (_req, res) => {
  const uptimeSeconds = Math.floor((Date.now() - START_TIME) / 1000);
  res.json({
    status:  "ok",
    uptime:  uptimeSeconds,
    uptimeHuman: `${Math.floor(uptimeSeconds / 3600)}h ${Math.floor((uptimeSeconds % 3600) / 60)}m ${uptimeSeconds % 60}s`,
    db:      fs.existsSync(DB_PATH) ? "file:tasks.json" : "in-memory only",
    timestamp: new Date().toISOString(),
  });
});

// GET /system  — agent status + task breakdown
app.get("/system", (_req, res) => {
  const breakdown = {
    todo:        tasks.filter((t) => t.status === "todo").length,
    "in-progress": tasks.filter((t) => t.status === "in-progress").length,
    done:        tasks.filter((t) => t.status === "done").length,
  };
  res.json({
    agents: {
      hermes:   { role: "planner",  status: agentBusy ? "planning" : "idle" },
      openclaw: { role: "executor", status: agentBusy ? "executing" : "idle" },
    },
    tasks: {
      total: tasks.length,
      breakdown,
    },
    cronInterval: "every 10 seconds",
    timestamp: new Date().toISOString(),
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Task CRUD API
// ─────────────────────────────────────────────────────────────────────────────
const VALID_STATUSES = ["todo", "in-progress", "done"];

// GET /tasks  — return all tasks (sorted oldest first)
app.get("/tasks", (_req, res) => {
  try {
    const sorted = [...tasks].sort(
      (a, b) => new Date(a.createdAt) - new Date(b.createdAt)
    );
    res.json(sorted);
  } catch (err) {
    log.error(`GET /tasks: ${err.message}`);
    res.status(500).json({ error: "Failed to retrieve tasks." });
  }
});

// POST /tasks  — create a new task
app.post("/tasks", (req, res) => {
  try {
    const { title } = req.body;

    if (!title || typeof title !== "string" || !title.trim()) {
      return res.status(400).json({
        error: "title is required and must be a non-empty string.",
      });
    }

    const task = {
      id:        uuidv4(),
      title:     title.trim(),
      status:    "todo",
      createdAt: new Date().toISOString(),
      updatedAt: null,
    };

    tasks.push(task);
    saveTasks(tasks);

    console.log(`📝  Created: "${task.title}" (${task.id})`);
    res.status(201).json(task);
  } catch (err) {
    log.error(`POST /tasks: ${err.message}`);
    res.status(500).json({ error: "Failed to create task." });
  }
});

// PATCH /tasks/:id  — update title and/or status
app.patch("/tasks/:id", (req, res) => {
  try {
    const { id } = req.params;
    const { title, status } = req.body;

    const task = tasks.find((t) => t.id === id);
    if (!task) {
      return res.status(404).json({ error: `Task "${id}" not found.` });
    }

    if (status !== undefined) {
      if (!VALID_STATUSES.includes(status)) {
        return res.status(400).json({
          error: `Invalid status. Must be one of: ${VALID_STATUSES.join(", ")}.`,
        });
      }
      task.status = status;
    }

    if (title !== undefined) {
      if (typeof title !== "string" || !title.trim()) {
        return res.status(400).json({ error: "title must be a non-empty string." });
      }
      task.title = title.trim();
    }

    task.updatedAt = new Date().toISOString();
    saveTasks(tasks);

    res.json(task);
  } catch (err) {
    log.error(`PATCH /tasks/${req.params.id}: ${err.message}`);
    res.status(500).json({ error: "Failed to update task." });
  }
});

// DELETE /tasks/:id  — delete a task
app.delete("/tasks/:id", (req, res) => {
  try {
    const { id } = req.params;
    const index = tasks.findIndex((t) => t.id === id);

    if (index === -1) {
      return res.status(404).json({ error: `Task "${id}" not found.` });
    }

    const [removed] = tasks.splice(index, 1);
    saveTasks(tasks);

    console.log(`🗑️   Deleted: "${removed.title}" (${removed.id})`);
    res.json({ message: "Task deleted successfully.", task: removed });
  } catch (err) {
    log.error(`DELETE /tasks/${req.params.id}: ${err.message}`);
    res.status(500).json({ error: "Failed to delete task." });
  }
});

// ── 404 catch-all ─────────────────────────────────────────────────────────────
app.use((req, res) => {
  res.status(404).json({ error: `Route ${req.method} ${req.path} not found.` });
});

// ── Global error handler ─────────────────────────────────────────────────────
app.use((err, _req, res, _next) => {
  log.error(`Unhandled error: ${err.message}`);
  res.status(500).json({ error: "Internal server error." });
});

// ─────────────────────────────────────────────────────────────────────────────
// AI Agent Simulation — Cron Job (every 10 seconds)
// ─────────────────────────────────────────────────────────────────────────────
let agentBusy = false;

cron.schedule("*/10 * * * * *", () => {
  try {
    // ── Busy guard — prevent overlapping agent runs ────────────────────────
    if (agentBusy) {
      log.system("Agent cycle skipped — previous job still running.");
      return;
    }

    // ── Pick the OLDEST todo task (stable, deterministic) ─────────────────
    const todoTasks = tasks
      .filter((t) => t.status === "todo")
      .sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));

    if (todoTasks.length === 0) {
      log.system("No todo tasks — agents idle.");
      return;
    }

    agentBusy = true;
    const target = todoTasks[0];

    // ── HERMES: Plan ──────────────────────────────────────────────────────
    console.log("");
    log.hermes(`Task selected  → "${target.title}" [id: ${target.id}]`);
    log.hermes(`Strategy       → todo → in-progress (now) → done (in 3s)`);

    // ── OPENCLAW: Begin execution — mark in-progress ──────────────────────
    const taskRef = tasks.find((t) => t.id === target.id);
    if (!taskRef) {
      log.error("Target task disappeared before execution.");
      agentBusy = false;
      return;
    }

    taskRef.status    = "in-progress";
    taskRef.updatedAt = new Date().toISOString();
    saveTasks(tasks);

    log.openclaw(`Executing      → "${taskRef.title}"`);
    log.openclaw(`Status changed → in-progress`);

    // ── OPENCLAW: Complete — mark done after 3 seconds ────────────────────
    setTimeout(() => {
      try {
        const t = tasks.find((t) => t.id === target.id);
        if (!t) {
          log.error("Task was deleted during execution — skipping completion.");
          agentBusy = false;
          return;
        }

        t.status    = "done";
        t.updatedAt = new Date().toISOString();
        saveTasks(tasks);

        log.openclaw(`Finished       → "${t.title}"`);
        log.result(`"${t.title}" completed successfully ✅`);
        console.log("");
      } catch (innerErr) {
        log.error(`Agent completion error: ${innerErr.message}`);
      } finally {
        agentBusy = false;
      }
    }, 3000);

  } catch (outerErr) {
    log.error(`Cron job crashed: ${outerErr.message}`);
    agentBusy = false; // always release lock
  }
});

// ─────────────────────────────────────────────────────────────────────────────
// Start Server
// ─────────────────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  const displayUrl = process.env.NODE_ENV === "production"
    ? "https://forge2-qualifier-abishek.onrender.com"
    : `http://localhost:${PORT}`;

  console.log("");
  console.log("╔══════════════════════════════════════════════════╗");
  console.log("║     AI Kanban Agent System  v2.0  — ONLINE       ║");
  console.log(`║     ${displayUrl.padEnd(44)} ║`);
  console.log("║     Database : tasks.json (file-based)           ║");
  console.log("║     Agents   : Hermes (planner) + OpenClaw (exec)║");
  console.log("║     Cron     : every 10 seconds                  ║");
  console.log("╚══════════════════════════════════════════════════╝");
  console.log("");
});