# 🔥 Forge Sprint 02 — Multi-Agent Slack System

**Submitted by:** Abishek R  
**Repo:** `forge2-qualifier-abishek`  

---

## 🧠 Project Overview

This repository demonstrates a **production-like multi-agent system** coordinated through **Slack**, built for the Forge 2 Sprint 02 qualifier challenge.

Two specialized AI agents cooperate to solve tasks seamlessly over Slack:
1. **Hermes** (Orchestrator / Brain)
2. **OpenClaw** (Coding Agent / Execution)

---

## 🏗️ Architecture & Workflow

```mermaid
flowchart TD
    User["👤 User (Slack #commands)"] -->|"posts task"| Hermes

    subgraph HermesAgent["🧠 Hermes — Orchestrator (Groq Kimi K2)"]
        Hermes["Receives task"]
        Memory["🗃️ Persistent Memory"]
        Skills["⚡ Skills Loader"]
        Hermes --> Memory
        Hermes --> Skills
        Hermes -->|"generates plan"| OrchChannel["#agent-orchestrator"]
    end

    OrchChannel -->|"reads plan"| OpenClaw

    subgraph OpenClawAgent["🦾 OpenClaw — Coding Agent (Ollama Qwen2.5-Coder)"]
        OpenClaw["Generates Python code"]
        Sandbox["▶️ Executes code locally"]
        Outputs["💾 Saves to outputs/"]
        GitPush["📦 Commits to GitHub"]
        
        OpenClaw --> Sandbox
        Sandbox --> Outputs
        Outputs --> GitPush
    end

    OpenClaw -->|"posts structured report"| LogChannel["#agent-log"]

    LogChannel -->|"reads report"| HermesValidate["🧠 Hermes — Validator"]
    
    HermesValidate -->|"Validates result.
    If fail: requests 1 revision.
    If pass: posts final to"| ReviewChannel["#human-review"]

    ReviewChannel -->|"sees final result"| Human["👤 Human Reviewer"]
```

### Communication Rules
- **All communication happens via Slack**. There are no direct API calls between agents.
- **#commands**: User posts new tasks here.
- **#agent-orchestrator**: Hermes posts step-by-step plans assigning work to OpenClaw.
- **#agent-log**: OpenClaw posts execution results in a structured format (`What I Did / What Failed / What Needs Review`).
- **#human-review**: Hermes posts the final validated results for human approval.

---

## 🤖 Agent Roles & Model Routing

| Agent | Role | Model | Responsibility |
|-------|------|-------|----------------|
| **Hermes** | Orchestrator | Groq Kimi K2 | Listens to users, checks memory & skills, plans tasks, assigns to OpenClaw, validates results. |
| **OpenClaw** | Execution | Ollama Qwen2.5-Coder | Listens for plans, writes code, executes it, pushes results to GitHub, reports status. |

*Reasoning for routing:* Hermes uses a strong cloud model (Groq/Kimi K2) for complex planning and validation. OpenClaw uses a fast, free local coding model (Ollama/Qwen2.5-Coder) for code execution and file manipulation.

---

## 📁 Project Structure

```
forge2-qualifier-abishek/
├── README.md                    ← You are here
├── run_system.py                ← Main launcher for both agents or demo mode
├── requirements.txt             ← Python dependencies
├── .env.example                 ← Environment template
├── agents/
│   ├── hermes.py                ← Hermes Slack Bot & Orchestrator
│   ├── openclaw.py              ← OpenClaw Slack Bot & Execution Engine
│   └── skills_loader.py         ← Parses YAML skills and matches triggers
├── memory/
│   └── hermes_memory.json       ← Persistent memory store for Hermes
├── outputs/                     ← Generated files from OpenClaw
├── skills/                      ← Markdown/YAML skills for Hermes
└── tests/
    └── test_agents.py           ← CI/CD style validation tests
```

---

## ⚙️ Setup & Run Instructions

### Prerequisites
1. Python 3.10+
2. Slack Workspace with a configured Bot (Bot Token + App-Level Token for Socket Mode).
3. Groq API Key
4. Ollama installed locally (`ollama pull qwen2.5-coder`)
5. GitHub Personal Access Token (for auto-commits)

### 1. Installation
```powershell
git clone https://github.com/Abishek2207/forge2-qualifier-abishek.git
cd forge2-qualifier-abishek
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configuration
Copy `.env.example` to `.env` and fill in your Slack tokens, Groq key, and GitHub token.
Create the required Slack channels in your workspace: `#commands`, `#agent-orchestrator`, `#agent-log`, `#human-review`.

### 3. Run the Agents
To run both agents simultaneously in Slack Socket Mode:
```powershell
python run_system.py
```

### 4. Run Demo Mode (No Slack Required)
If you just want to see the workflow logic run locally in the terminal:
```powershell
python run_system.py --demo
```

### 5. Run CI/CD Tests
```powershell
pytest tests/
```

---

## 🎥 60–90s Demo Workflow

To demonstrate this system for the qualifier:
1. Start the agents (`python run_system.py`).
2. Open Slack. Go to `#commands`.
3. Type: `Fetch the titles from python.org and groq.com and save to outputs/demo.json`
4. Watch `#agent-orchestrator`. Hermes will immediately post a structured plan and assign it to OpenClaw.
5. Watch `#agent-log`. OpenClaw will generate code, execute it locally, commit to GitHub, and post a report.
6. Hermes will read the report, validate it, and post the final verdict to `#human-review`. 

---
**Author:** Abishek R  
*Built for Forge 2 Sprint 02*
