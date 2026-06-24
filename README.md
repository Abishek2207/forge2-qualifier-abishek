# AI Kanban Agent System

> **Forge 2 Qualifier Submission** · Full-stack AI-powered Kanban board with autonomous Hermes + OpenClaw agent simulation.

---

## 🌐 Live Deployment

| Service | URL |
|---------|-----|
| **Backend API (Render)** | https://forge2-qualifier-abishek.onrender.com |
| **Frontend UI (Vercel)** | _(set after Vercel import)_ |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                             │
│                    React + Vite (Vercel)                        │
│                                                                 │
│  ┌───────────┐   ┌───────────┐   ┌───────────┐                 │
│  │   To Do   │   │   Doing   │   │   Done    │  ← Kanban UI    │
│  └───────────┘   └───────────┘   └───────────┘                 │
│        │               │               │                        │
│        └───────────────┴───────────────┘                       │
│                         │  fetch (every 4s poll)               │
└─────────────────────────┼───────────────────────────────────────┘
                          │ HTTPS REST API
┌─────────────────────────▼───────────────────────────────────────┐
│                  Node.js + Express (Render)                     │
│                                                                 │
│   ┌──────────────┐     ┌──────────────────────────────────┐    │
│   │  REST CRUD   │     │     Cron Agent Loop (10s)        │    │
│   │  GET /tasks  │     │                                  │    │
│   │  POST /tasks │     │  [HERMES]   → plan task          │    │
│   │  PATCH /:id  │     │  [OPENCLAW] → execute (3s)       │    │
│   │  DELETE /:id │     │  [RESULT]   → mark done          │    │
│   └──────┬───────┘     └──────────────┬───────────────────┘    │
│          │                            │                         │
│          └────────────┬───────────────┘                         │
│                       ▼                                         │
│              ┌─────────────────┐                                │
│              │   tasks.json    │  ← File-based persistence      │
│              │  (atomic write) │     (write → .tmp → rename)    │
│              └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Agent Architecture (Hermes + OpenClaw)

### Design Pattern: Planner–Executor

| Agent | Role | Behaviour |
|-------|------|-----------|
| **Hermes** | Planner | Selects the oldest `todo` task every 10 seconds. Logs its decision and strategy. |
| **OpenClaw** | Executor | Receives the task from Hermes. Marks it `in-progress`, waits 3 seconds (simulated execution), marks it `done`. |

### Why this simulates real agent routing

In a production multi-agent system, Hermes would query an LLM router to decide *which* agent and *what skill* to invoke. OpenClaw would call external tools (APIs, code runners, browsers). Here, the cron job simulates this loop deterministically — the **architecture is identical**, only the LLM call is replaced by a `setTimeout`.

### Console Log Format

```
[HERMES]   Task selected  → "Build login page" [id: uuid]
[HERMES]   Strategy       → todo → in-progress (now) → done (in 3s)
[OPENCLAW] Executing      → "Build login page"
[OPENCLAW] Status changed → in-progress
[OPENCLAW] Finished       → "Build login page"
[RESULT]   "Build login page" completed successfully ✅
```

### Model Routing (Documented)

```
User creates task
     │
     ▼
Hermes (Planner)
  └─ Would call: GPT-4o / Gemini Pro for task decomposition
  └─ In simulation: picks oldest todo task deterministically
     │
     ▼
OpenClaw (Executor)
  └─ Would call: tool-use APIs, browser, code interpreter
  └─ In simulation: setTimeout(3000) simulates async execution
     │
     ▼
Result written to tasks.json (persistent)
     │
     ▼
Frontend polls every 4s → UI updates automatically
```

---

## 🗂️ Project Structure

```
forge2-qualifier-abishek/
├── render.yaml                   ← Render auto-deploy config
├── README.md
│
├── backend/
│   ├── server.js                 ← Express + CRUD + Cron agent
│   ├── tasks.json                ← File-based database (seed + live data)
│   ├── package.json
│   └── .gitignore
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── vercel.json               ← Vercel deploy config + SPA rewrites
    ├── .env.example              ← Environment variable template
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx               ← Kanban UI + API integration
        └── index.css             ← Premium dark design system
```

---

## 🚀 Local Development

### 1. Clone & Run Backend

```bash
cd backend
npm install
npm start
# → http://localhost:3000
```

### 2. Run Frontend

```bash
cd frontend
cp .env.example .env.local       # uses localhost:3000 for dev
npm install
npm run dev
# → http://localhost:5173
```

---

## 📡 API Reference

| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| `GET` | `/` | — | System info + agent status |
| `GET` | `/health` | — | Uptime (Render health check) |
| `GET` | `/system` | — | Agent state + task breakdown |
| `GET` | `/tasks` | — | All tasks (sorted oldest first) |
| `POST` | `/tasks` | `{ title }` | Create task → `todo` |
| `PATCH` | `/tasks/:id` | `{ status?, title? }` | Update task |
| `DELETE` | `/tasks/:id` | — | Delete task |

**Valid statuses:** `todo` · `in-progress` · `done`

---

## 🛡️ Safety & Reliability

| Concern | Solution |
|---------|----------|
| File corruption on crash | Atomic write: `.tmp` → `rename` |
| Missing `tasks.json` | `loadTasks()` returns `[]` safely |
| Malformed JSON in file | `try/catch` → returns `[]` |
| Cron race conditions | `agentBusy` mutex lock |
| Task deleted mid-execution | `find()` null-check before completion |
| Express crashes | Global `app.use(err)` handler |
| Unknown routes | 404 JSON catch-all |

---

## ☁️ Deployment

### Backend → Render

**Via `render.yaml` (Blueprint, automatic):**
1. New → Blueprint → Connect `Abishek2207/forge2-qualifier-abishek`
2. Render reads `render.yaml` and configures everything

**Manual setup:**

| Field | Value |
|-------|-------|
| Root Directory | `backend` |
| Build Command | `npm install` |
| Start Command | `npm start` |
| Health Check Path | `/health` |
| Environment Variable | `NODE_ENV=production` |

### Frontend → Vercel

1. Import `Abishek2207/forge2-qualifier-abishek`
2. Root Directory → `frontend`
3. Framework → **Vite** (auto-detected)
4. Add environment variable:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://forge2-qualifier-abishek.onrender.com` |

5. Deploy ✅

---

## ✅ Forge 2 Judging Checklist

| Requirement | Status |
|-------------|--------|
| Working Kanban UI | ✅ To Do / Doing / Done columns |
| Real backend (no localStorage) | ✅ File-based JSON persistence |
| Create / Move / Delete tasks | ✅ Full CRUD via REST API |
| Agent simulation (Hermes + OpenClaw) | ✅ node-cron every 10s |
| Agent logs visible | ✅ Coloured console output |
| Cron auto-moves tasks | ✅ todo → in-progress → done |
| UI auto-refreshes | ✅ Polling every 4 seconds |
| Model routing documented | ✅ Architecture section above |
| CI/CD ready | ✅ render.yaml + vercel.json |
| No runtime crashes | ✅ Full try/catch coverage |
| Render deployable | ✅ Live at onrender.com |
| Vercel deployable | ✅ vercel.json + env vars |
| Health check endpoint | ✅ GET /health |
| No hardcoded localhost in production | ✅ VITE_API_URL env var |

---

## ⚠️ Common Mistakes Avoided

| Mistake | Fix Applied |
|---------|------------|
| `localStorage` usage | Strictly forbidden — all state from backend |
| Hardcoded `localhost` in production frontend | `VITE_API_URL` env var with Render fallback |
| `tasks.json` data loss on crash | Atomic write with `.tmp` + `rename` |
| Cron overlap (race condition) | `agentBusy` boolean mutex |
| Random task selection (unpredictable) | Oldest-first sort — deterministic |
| Missing error boundaries | `try/catch` on every async operation |
| Blocking cron with `await` in `setTimeout` | Synchronous update before `setTimeout` |
| Missing 404 handler | Catch-all JSON route at bottom of app |
| Frontend crashes on fetch error | Error state UI with Retry button |
| No CORS on backend | `cors()` middleware applied globally |
