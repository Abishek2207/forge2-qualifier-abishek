import { useState, useEffect, useCallback, useRef } from "react";

const API = import.meta.env.VITE_API_URL || "https://forge2-qualifier-abishek.onrender.com";

// ─── Helpers ──────────────────────────────────────────────────────────────────
function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function useToast() {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = "success") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3500);
  }, []);

  return { toasts, addToast };
}

// ─── Task Card ────────────────────────────────────────────────────────────────
function TaskCard({ task, onDelete, onMove }) {
  const isDone    = task.status === "done";
  const isDoing   = task.status === "in-progress";

  return (
    <div className={`task-card ${isDone ? "task-card--done" : ""}`} id={`task-${task.id}`}>
      <p className="task-title">{task.title}</p>

      {isDoing && (
        <div>
          <span className="agent-tag agent-tag--doing">⚡ OpenClaw executing…</span>
        </div>
      )}

      <div className="task-footer">
        <div className="task-actions">
          {/* Move backward */}
          {task.status === "in-progress" && (
            <button
              className="task-btn task-btn--back"
              onClick={() => onMove(task.id, "todo")}
              title="Move back to To Do"
            >
              ← To Do
            </button>
          )}
          {task.status === "done" && (
            <button
              className="task-btn task-btn--back"
              onClick={() => onMove(task.id, "in-progress")}
              title="Move back to Doing"
            >
              ← Doing
            </button>
          )}

          {/* Move forward */}
          {task.status === "todo" && (
            <button
              className="task-btn task-btn--forward"
              onClick={() => onMove(task.id, "in-progress")}
              title="Move to Doing"
            >
              Start →
            </button>
          )}
          {task.status === "in-progress" && (
            <button
              className="task-btn task-btn--forward"
              onClick={() => onMove(task.id, "done")}
              title="Mark as Done"
            >
              Done →
            </button>
          )}

          <button
            className="task-btn task-btn--delete"
            onClick={() => onDelete(task.id)}
            title="Delete task"
          >
            ✕
          </button>
        </div>

        <span className="task-time">{formatTime(task.updatedAt || task.createdAt)}</span>
      </div>
    </div>
  );
}

// ─── Column ───────────────────────────────────────────────────────────────────
function Column({ id, label, tasks, onDelete, onMove }) {
  const colClass = {
    todo:          "column--todo",
    "in-progress": "column--doing",
    done:          "column--done",
  }[id];

  const emptyIcons = {
    todo:          "📭",
    "in-progress": "⏳",
    done:          "🏆",
  };

  return (
    <div className={`column ${colClass}`} id={`column-${id}`}>
      <div className="column-header">
        <div className="column-title-group">
          <div className="column-dot" />
          <span className="column-name">{label}</span>
        </div>
        <span className="column-count">{tasks.length}</span>
      </div>

      <div className="column-body">
        {tasks.length === 0 ? (
          <div className="column-empty">
            <span>{emptyIcons[id]}</span>
            <span>No tasks here</span>
          </div>
        ) : (
          tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onDelete={onDelete}
              onMove={onMove}
            />
          ))
        )}
      </div>
    </div>
  );
}

// ─── Toast Container ──────────────────────────────────────────────────────────
function ToastContainer({ toasts }) {
  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast--${t.type}`}>
          {t.message}
        </div>
      ))}
    </div>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [tasks,   setTasks]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  const [input,   setInput]   = useState("");
  const [creating, setCreating] = useState(false);
  const { toasts, addToast }  = useToast();
  const pollRef = useRef(null);

  // ── Fetch all tasks ──────────────────────────────────────────────────────
  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch(`${API}/tasks`);
      if (!res.ok) throw new Error(`Server responded ${res.status}`);
      const data = await res.json();
      setTasks(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Initial load + polling every 4 s ────────────────────────────────────
  useEffect(() => {
    fetchTasks();
    pollRef.current = setInterval(fetchTasks, 4000);
    return () => clearInterval(pollRef.current);
  }, [fetchTasks]);

  // ── Create task ──────────────────────────────────────────────────────────
  const handleCreate = async (e) => {
    e.preventDefault();
    const title = input.trim();
    if (!title) return;

    setCreating(true);
    try {
      const res = await fetch(`${API}/tasks`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ title }),
      });
      if (!res.ok) {
        const body = await res.json();
        throw new Error(body.error || "Failed to create task");
      }
      const created = await res.json();
      setTasks((prev) => [...prev, created]);
      setInput("");
      addToast(`Task "${created.title}" created ✓`, "success");
    } catch (err) {
      addToast(err.message, "error");
    } finally {
      setCreating(false);
    }
  };

  // ── Move task ────────────────────────────────────────────────────────────
  const handleMove = async (id, status) => {
    // Optimistic update
    setTasks((prev) => prev.map((t) => t.id === id ? { ...t, status, updatedAt: new Date().toISOString() } : t));

    try {
      const res = await fetch(`${API}/tasks/${id}`, {
        method:  "PATCH",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error("Failed to update task");
      const updated = await res.json();
      setTasks((prev) => prev.map((t) => t.id === id ? updated : t));
    } catch (err) {
      addToast(err.message, "error");
      fetchTasks(); // revert
    }
  };

  // ── Delete task ──────────────────────────────────────────────────────────
  const handleDelete = async (id) => {
    const task = tasks.find((t) => t.id === id);
    // Optimistic remove
    setTasks((prev) => prev.filter((t) => t.id !== id));

    try {
      const res = await fetch(`${API}/tasks/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete task");
      addToast(`Task deleted ✓`, "success");
    } catch (err) {
      addToast(err.message, "error");
      fetchTasks(); // revert
    }
  };

  // ── Derived columns ──────────────────────────────────────────────────────
  const todo    = tasks.filter((t) => t.status === "todo");
  const doing   = tasks.filter((t) => t.status === "in-progress");
  const done    = tasks.filter((t) => t.status === "done");

  const totalCount = tasks.length;

  // ── Render ───────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="app">
        <div className="center-screen">
          <div className="spinner" />
          <p>Connecting to agent system…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app">
        <div className="center-screen">
          <div className="error-box">
            <h2>⚠ Connection Error</h2>
            <p>Cannot reach backend at <code>http://localhost:3000</code></p>
            <p style={{ marginTop: 6 }}>{error}</p>
            <button className="retry-btn" onClick={fetchTasks}>Retry</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="header-brand">
          <div className="header-icon">🤖</div>
          <div className="header-text">
            <h1>AI Kanban Agent System</h1>
            <p>Powered by Hermes &amp; OpenClaw agents</p>
          </div>
        </div>
        <div className="header-meta">
          <div className="status-badge">
            <div className="status-dot" />
            Agents Online
          </div>
          <div className="task-count-badge">{totalCount} task{totalCount !== 1 ? "s" : ""}</div>
        </div>
      </header>

      {/* ── Create Task Form ── */}
      <section className="create-section" aria-label="Create task">
        <form className="create-form" onSubmit={handleCreate} id="create-task-form">
          <input
            id="task-title-input"
            className="create-input"
            type="text"
            placeholder="Describe a task for the agents…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={creating}
            autoComplete="off"
            maxLength={200}
          />
          <button
            id="create-task-btn"
            className="create-btn"
            type="submit"
            disabled={creating || !input.trim()}
          >
            {creating ? "Creating…" : "＋ Add Task"}
          </button>
        </form>
      </section>

      {/* ── Kanban Board ── */}
      <main className="board" aria-label="Kanban board">
        <Column id="todo"        label="To Do"  tasks={todo}  onDelete={handleDelete} onMove={handleMove} />
        <Column id="in-progress" label="Doing"  tasks={doing} onDelete={handleDelete} onMove={handleMove} />
        <Column id="done"        label="Done"   tasks={done}  onDelete={handleDelete} onMove={handleMove} />
      </main>

      {/* ── Toasts ── */}
      <ToastContainer toasts={toasts} />
    </div>
  );
}
