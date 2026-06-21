# Forge 2 Edition 1 Qualifier

Hi, I'm Abishek R. I built this repository to participate in the Forge 2 Edition 1 qualifier challenge. This project demonstrates a multi-agent system coordinated through Slack to fulfill both the OpenClaw Mastery and Hermes Mastery requirements (Starter 1 and Starter 2), as well as a full React Kanban board built by the agents.

## Live Application
**Live URL**: `[INSERT_VERCEL_LIVE_URL_HERE]`

## Architecture & Roles

**Hermes (Brain / Orchestrator)**: It receives tasks, formulates a plan, checks its memory and skills, and delegates work to OpenClaw. It validates results before human review.
**OpenClaw (Hands / Coding Agent)**: It takes instructions from Hermes, generates code, runs it locally, and reports the results back to Slack.

## Slack Workflow
1. User posts a task in `#commands` or `#sprint-main`.
2. Hermes receives the task, generates a plan, and posts it to `#agent-orchestrator`.
3. OpenClaw executes the task, saving output locally, and posts a structured status report to `#agent-log`.
4. Hermes validates the execution and posts the final output to `#human-review`.

## Tech Stack & Models Used
* **Free Stack**: React, Vite, Node, LocalStorage, GitHub, Vercel/Netlify.
* **Hermes Model**: Groq / Gemini free model (for planning).
* **OpenClaw Model**: Ollama Qwen2.5-Coder (for local execution).

## Evidence Mapping
See `EVIDENCE.md` for a complete mapping of requirements to repository proofs.

## Kanban App Features
We built a tiny Trello-style Kanban board in the `frontend/` directory with the following features:
- [x] Boards
- [x] Lists inside a board: To Do, Doing, Done
- [x] Cards inside lists
- [x] Move a card between lists (Drag & Drop)
- [x] Card title + description editing
- [x] Colored tags/labels
- [x] Members and assign member to card
- [x] Due date and overdue visual flag

## How to Run Locally

### Prerequisites
1. Python 3.10+
2. Node.js 18+
3. A Slack workspace with a Bot Token and App-Level Token.
4. Local Ollama if using local models (`ollama pull qwen2.5-coder`).

### Installation
```bash
git clone https://github.com/Abishek2207/forge2-qualifier-abishek.git
cd forge2-qualifier-abishek

# Backend/Agent setup
python -m venv .venv
# Activate venv
pip install -r requirements.txt
```

### Configuration
Copy `.env.example` to `.env` and fill in your keys. Create the necessary Slack channels.

### Run the Agents
```bash
python run_system.py
```

### Run the Frontend
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` to view the Kanban board.
