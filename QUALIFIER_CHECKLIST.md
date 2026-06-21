# Forge 2 Qualifier Checklist

## Required Files & Directories
- [x] `README.md` present
- [x] `ARCHITECTURE.md` present
- [x] `EVIDENCE.md` present
- [x] `agent-log.md` present
- [x] `slack-export/` present
- [x] `screenshots/` present
- [x] `skills/` present
- [x] `backend/` Laravel present
- [x] `frontend/` React present
- [x] `.env.example` present
- [x] Live URL present

## Agent Features
- [x] **Task execution**: OpenClaw loop documented in `agent-log.md`
- [x] **Memory**: Hermes uses `memory/hermes_memory.json`
- [x] **Skill**: Predefined skills exist in `skills/`
- [x] **Autonomous run**: Outputs available in `outputs/autonomous-run.txt`
- [x] **Live URL**: Included in `README.md`
- [x] **Slack proof**: Screenshots mapped in `screenshots/README.md`

## Kanban App Features
- [x] **Boards**: Implemented in React frontend
- [x] **Lists**: To Do, Doing, Done lists
- [x] **Cards**: Cards exist inside lists
- [x] **Drag & Drop**: Move cards between lists
- [x] **Card Editing**: Edit card title and description
- [x] **Tags/Labels**: Colored tags on cards
- [x] **Members**: Assign members to cards
- [x] **Due Date**: Set due dates and flag overdue visually
