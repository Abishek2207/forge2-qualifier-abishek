# AI Kanban Agent System

A full-stack, production-ready AI-powered Kanban board with simulated Hermes (planner) and OpenClaw (executor) agents.

---

## Project Structure

```
forge2-qualifier-abishek/
├── backend/
│   ├── server.js       ← Express server + CRUD + Cron agent
│   └── package.json
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx
        └── index.css
```

---

## Quick Start

### 1. Backend

```bash
cd backend
npm install
npm start
```

Backend starts on **http://localhost:3000**

### 2. Frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend starts on **http://localhost:5173**

---

## API Reference

| Method | Endpoint      | Body                        | Description        |
|--------|---------------|-----------------------------|--------------------|
| GET    | /tasks        | —                           | List all tasks     |
| POST   | /tasks        | `{ title: string }`        | Create task        |
| PATCH  | /tasks/:id    | `{ status?, title? }`      | Update task        |
| DELETE | /tasks/:id    | —                           | Delete task        |
| GET    | /health       | —                           | Health check       |

Valid statuses: `todo` · `in-progress` · `done`

---

## Agent Behavior

The cron job fires every **10 seconds**:

1. **HERMES** picks a random `todo` task and plans execution.
2. **OPENCLAW** moves it to `in-progress` immediately.
3. After **3 seconds**, task is marked `done`.

Console output example:
```
[HERMES]    Task selected  → "Design system architecture" (id: abc-123)
[HERMES]    Plan           → Mark in-progress → execute → mark done
[OPENCLAW]  Executing task → "Design system architecture"
[OPENCLAW]  Status changed → in-progress
[OPENCLAW]  Task finished  → "Design system architecture"
[RESULT]    "Design system architecture" completed successfully ✅
```

---

## Deployment

### Backend → Render

1. Push `backend/` to a GitHub repo.
2. New Web Service → Build command: `npm install` → Start command: `npm start`.
3. Set `PORT` env var if needed (defaults to 3000).

### Frontend → Vercel

1. Push `frontend/` to a GitHub repo.
2. Import in Vercel → Framework: Vite → Build: `npm run build` → Output: `dist`.
3. Update `const API = "https://your-render-backend.onrender.com"` in `App.jsx` before deploying.
