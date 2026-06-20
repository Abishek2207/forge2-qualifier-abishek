---
name: forge-status
description: >
  Reports the current status of the Forge 2 qualifier project.
  Triggers when the user asks about qualifier status, agent progress,
  submission readiness, or task completion. Reads agent-log.md,
  outputs/results.json, and outputs/autonomous-run.txt to build
  a structured status report.
triggers:
  - qualifier status
  - agent progress
  - what's our status
  - forge status
  - submission ready
  - how are we doing
  - what did openclaw do
  - what's done
---

# Forge Status Skill

## Purpose

This skill is triggered whenever the user (or another agent) asks about the current state of the Forge 2 qualifier submission. It acts as a **live dashboard** that Hermes can pull up at any time to answer questions like:

- "What's done?"
- "What's left before we can submit?"
- "Did the autonomous run succeed?"
- "Is the repo ready for the qualifier?"

---

## Trigger Patterns

Hermes fires this skill when the user's message matches any of these patterns (case-insensitive, partial match is fine):

| Pattern | Example Input |
|---------|--------------|
| `qualifier status` | "What's the qualifier status?" |
| `agent progress` | "What's the agent progress so far?" |
| `what's our status` | "Hey Hermes, what's our status?" |
| `forge status` | "Give me a forge status" |
| `submission ready` | "Are we submission ready?" |
| `how are we doing` | "How are we doing on this?" |
| `what did openclaw do` | "What did OpenClaw do today?" |
| `what's done` | "What's done so far?" |

---

## Execution Steps

When triggered, Hermes executes the following steps in order:

### Step 1 — Read Agent Log
```
Read: agent-log.md
Extract: All session summaries (Sessions 1–5)
Parse: ✅ / ⏳ status markers from the summary table
```

### Step 2 — Check Output Files
```
Check: outputs/results.json
  → exists? yes/no
  → valid JSON? yes/no
  → record count?

Check: outputs/autonomous-run.txt
  → exists? yes/no
  → timestamp present? yes/no
```

### Step 3 — Build Status Report

Hermes formats and returns a report like this:

```
📊 FORGE 2 QUALIFIER STATUS REPORT
════════════════════════════════════════
Project  : Forge 2 Edition 1 Qualifier
Agent    : Hermes (orchestrator) + OpenClaw (coding)
Time     : [current timestamp]

TASK COMPLETIONS:
  ✅  Session 1 — OpenClaw Task Loop
  ✅  Session 2 — Revision Loop
  ✅  Session 3 — Hermes Memory Test
  ✅  Session 4 — Hermes Skill Firing     ← (this run!)
  ✅  Session 5 — Autonomous Run Proof

OUTPUT FILES:
  ✅  outputs/results.json       → [n] URLs fetched
  ✅  outputs/autonomous-run.txt → timestamp confirmed

NEXT STEPS:
  ⏳  Add screenshots to screenshots/
  ⏳  Record Loom video
  ⏳  git push to GitHub (public repo)
  ⏳  Submit to Forge 2

VERDICT: Repo is submission-ready pending screenshots & video.
════════════════════════════════════════
```

---

## Notes for Demo

- When showing this skill to a Forge 2 reviewer, ask Hermes: *"What's our qualifier status?"*
- The skill fires within 1–2 seconds (no API call required — reads local files only)
- This demonstrates **skill-based automation** — Hermes is not just a chatbot, it has structured responses for known query types
- The skill can be extended to also post to Slack/Discord by adding a `notify` action in the skill body

---

## Skill Author

- **Defined by:** Abishek R
- **Agent:** Hermes
- **Skill type:** Status / Reporting
- **Model dependency:** None (Hermes reads files locally; no LLM call required for this skill)
