# Evidence Mapping

This document maps the Forge 2 Qualifier handbook requirements to the specific files, screenshots, and proofs in this repository.

## Starter 1: OpenClaw Mastery

| Requirement | Evidence File | Screenshot Location | Proof Source |
|-------------|---------------|---------------------|--------------|
| Task execution | `agent-log.md` (Session 1) | `screenshots/` | Code outputs are saved in `outputs/results.json` and task files in `outputs/`. |
| Revision loop | `agent-log.md` (Session 2) | `screenshots/` | Hermes requesting a fix for timeout handling and OpenClaw modifying the script. |
| Status reporting | `agent-log.md` (Session 1 & 2) | `screenshots/` | Strict adherence to "What I Did / What's Left / What Needs Your Call" in `#agent-log`. |

## Starter 2: Hermes Mastery

| Requirement | Evidence File | Screenshot Location | Proof Source |
|-------------|---------------|---------------------|--------------|
| Memory | `memory/hermes_memory.json` | `screenshots/` | `agent-log.md` Session 3 details Hermes retrieving user goals from JSON. |
| Skill | `skills/` | `screenshots/` | `agent-log.md` Session 4 details the `hello-world` and `forge-status` skill triggers. |
| Plan before action | `agent-log.md` (Session 1) | `screenshots/` | Hermes posts the generated plan to `#agent-orchestrator` before OpenClaw executes. |
| Autonomous run | `outputs/autonomous-run.txt` | `screenshots/` | `agent-log.md` Session 5 shows the scheduled execution of `scripts/autonomous_status.py`. |

## What I Learned

Building this qualifier was a great learning experience. As a student builder, I realized that getting two LLMs to coordinate reliably is much harder than it sounds. 
Initially, the agents would hallucinate each other's roles or lose track of the task. By forcing them to communicate strictly through Slack channels with a structured format, I was able to build a much more stable system. 
I also learned the value of a "Plan before action" step. When Hermes was forced to write down its plan in `#agent-orchestrator`, it made fewer mistakes and gave OpenClaw much clearer instructions.
Implementing the memory and skills systems taught me how to give agents long-term context without bloating the prompt.
