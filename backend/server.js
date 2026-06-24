const express = require("express");
const cors = require("cors");
const cron = require("node-cron");
const { v4: uuidv4 } = require("uuid");

const app = express();
const PORT = process.env.PORT || 3000;

// ─── Middleware ───────────────────────────────────────────────────────────────
app.use(cors());
app.use(express.json());

// ─── In-Memory Database ───────────────────────────────────────────────────────
let tasks = [
  { id: uuidv4(), title: "Design system architecture", status: "todo", createdAt: new Date().toISOString() },
  { id: uuidv4(), title: "Set up CI/CD pipeline",      status: "todo", createdAt: new Date().toISOString() },
  { id: uuidv4(), title: "Write API documentation",    status: "todo", createdAt: new Date().toISOString() },
];

// ─── Utility: Coloured Console Logging ───────────────────────────────────────
const RESET  = "\x1b[0m";
const CYAN   = "\x1b[36m";
const YELLOW = "\x1b[33m";
const GREEN  = "\x1b[32m";
const RED    = "\x1b[31m";
const BOLD   = "\x1b[1m";

function logHermes(msg)   { console.log(`${CYAN}${BOLD}[HERMES]${RESET}    ${msg}`);   }
function logOpenClaw(msg) { console.log(`${YELLOW}${BOLD}[OPENCLAW]${RESET}  ${msg}`); }
function logResult(msg)   { console.log(`${GREEN}${BOLD}[RESULT]${RESET}    ${msg}`);   }
function logSystem(msg)   { console.log(`${RED}${BOLD}[SYSTEM]${RESET}    ${msg}`);     }

// ─── REST API ─────────────────────────────────────────────────────────────────

// GET /tasks  — return all tasks
app.get("/tasks", (req, res) => {
  res.json(tasks);
});

// POST /tasks  — create a new task
app.post("/tasks", (req, res) => {
  const { title } = req.body;
  if (!title || typeof title !== "string" || !title.trim()) {
    return res.status(400).json({ error: "title is required and must be a non-empty string" });
  }
  const task = {
    id:        uuidv4(),
    title:     title.trim(),
    status:    "todo",
    createdAt: new Date().toISOString(),
  };
  tasks.push(task);
  console.log(`\n📝  New task created: "${task.title}" (${task.id})\n`);
  res.status(201).json(task);
});

// PATCH /tasks/:id  — update status and/or title
app.patch("/tasks/:id", (req, res) => {
  const { id } = req.params;
  const { status, title } = req.body;

  const VALID_STATUSES = ["todo", "in-progress", "done"];

  const task = tasks.find((t) => t.id === id);
  if (!task) {
    return res.status(404).json({ error: `Task with id "${id}" not found` });
  }

  if (status !== undefined) {
    if (!VALID_STATUSES.includes(status)) {
      return res.status(400).json({ error: `status must be one of: ${VALID_STATUSES.join(", ")}` });
    }
    task.status = status;
  }

  if (title !== undefined) {
    if (typeof title !== "string" || !title.trim()) {
      return res.status(400).json({ error: "title must be a non-empty string" });
    }
    task.title = title.trim();
  }

  task.updatedAt = new Date().toISOString();
  res.json(task);
});

// DELETE /tasks/:id  — delete a task
app.delete("/tasks/:id", (req, res) => {
  const { id } = req.params;
  const index = tasks.findIndex((t) => t.id === id);
  if (index === -1) {
    return res.status(404).json({ error: `Task with id "${id}" not found` });
  }
  const [removed] = tasks.splice(index, 1);
  console.log(`\n🗑️   Task deleted: "${removed.title}" (${removed.id})\n`);
  res.json({ message: "Task deleted", task: removed });
});

// ─── CRON JOB: AI Agent Simulation ───────────────────────────────────────────
// Runs every 10 seconds. Hermes picks a "todo" task, OpenClaw executes it.

let agentBusy = false; // prevent overlapping runs

cron.schedule("*/10 * * * * *", () => {
  if (agentBusy) {
    logSystem("Agents are busy — skipping this cycle.");
    return;
  }

  const todoTasks = tasks.filter((t) => t.status === "todo");
  if (todoTasks.length === 0) {
    logSystem("No todo tasks available — agents idle.");
    return;
  }

  agentBusy = true;

  // ── Hermes: Plan ──────────────────────────────────────────────────────────
  const selected = todoTasks[Math.floor(Math.random() * todoTasks.length)];
  logHermes(`Task selected  → "${selected.title}" (id: ${selected.id})`);
  logHermes(`Plan           → Mark in-progress → execute → mark done`);

  // ── OpenClaw: Start Execution ─────────────────────────────────────────────
  selected.status    = "in-progress";
  selected.updatedAt = new Date().toISOString();
  logOpenClaw(`Executing task → "${selected.title}"`);
  logOpenClaw(`Status changed → in-progress`);

  // ── After 3 seconds: Complete ─────────────────────────────────────────────
  setTimeout(() => {
    const task = tasks.find((t) => t.id === selected.id);
    if (task) {
      task.status    = "done";
      task.updatedAt = new Date().toISOString();
      logOpenClaw(`Task finished  → "${task.title}"`);
      logResult(`"${task.title}" completed successfully ✅`);
    }
    agentBusy = false;
  }, 3000);
});

// ─── Health Check ─────────────────────────────────────────────────────────────
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    uptime: process.uptime(),
    taskCount: tasks.length,
    timestamp: new Date().toISOString(),
  });
});

// ─── Start Server ─────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log("");
  console.log("╔══════════════════════════════════════════════╗");
  console.log("║   AI Kanban Agent System — Backend Ready     ║");
  console.log(`║   Listening on http://localhost:${PORT}         ║`);
  console.log("║   Cron agent fires every 10 seconds          ║");
  console.log("╚══════════════════════════════════════════════╝");
  console.log("");
});
