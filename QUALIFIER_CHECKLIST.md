# Qualifier Submission Checklist
**Sprint 02 Starter 1 + Starter 2**

Before finalizing the submission for Forge 2 Edition 1 Qualifier, ensure the following criteria have been met and tested:

- [ ] **Hermes working**: Hermes correctly parses tasks in `#commands`, generates plans, and assigns them to `#agent-orchestrator`.
- [ ] **OpenClaw working**: OpenClaw reads `#agent-orchestrator`, executes code locally, and posts structured reports back to `#agent-log`.
- [ ] **Slack connected**: System successfully runs using Slack Socket Mode (`run_system.py`) and channels are correctly mapped.
- [ ] **Memory proof**: `memory/hermes_memory.json` persists project goals, builder name, and track histories.
- [ ] **Skill proof**: `skills/hello-world/SKILL.md` and `skills/forge-status/SKILL.md` triggers are working and firing correctly.
- [ ] **Autonomous run proof**: `outputs/autonomous-run.txt` has been generated with a valid timestamp and system health status.
- [ ] **Revision loop proof**: `agent-log.md` contains a documented revision sequence displaying Hermes feedback and OpenClaw corrections.
- [ ] **GitHub public**: The repository `Abishek2207/forge2-qualifier-abishek` is set to Public visibility.
- [ ] **Ready for submission**: All evidence files, code logic, and checklists are up to date and clean.
