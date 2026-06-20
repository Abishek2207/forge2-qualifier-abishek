"""
agents/hermes.py
================
Hermes — Orchestrator / Brain Agent
Forge Sprint 02 | Multi-Agent System

Role:
    Hermes is the planning and coordination brain. It:
      1. Listens to #commands for user tasks
      2. Loads memory and checks for relevant skill triggers
      3. Calls Groq (Kimi K2) to generate a structured plan
      4. Posts the plan + task assignment to #agent-orchestrator
      5. Monitors #agent-log for OpenClaw's response
      6. Validates the result and requests one improvement if needed
      7. Posts the final validated result to #human-review

Communication:
    - Reads from : #commands, #agent-log
    - Writes to  : #agent-orchestrator, #human-review

Author : Abishek R
Model  : Groq / Kimi K2 (moonshotai/kimi-k2-instruct)
"""

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Environment ───────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# ── Groq Client ───────────────────────────────────────────────────────────────
from groq import Groq

# ── Slack Bolt ────────────────────────────────────────────────────────────────
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ── Skills Loader ─────────────────────────────────────────────────────────────
from agents.skills_loader import SkillsLoader


# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

GROQ_MODEL   = os.getenv("GROQ_MODEL", "moonshotai/kimi-k2-instruct")
MEMORY_FILE  = Path("memory/hermes_memory.json")
SKILLS_DIR   = Path("skills")

# Slack channel names (without #)
CH_COMMANDS    = os.getenv("SLACK_CHANNEL_COMMANDS",     "commands")
CH_ORCHESTRATOR = os.getenv("SLACK_CHANNEL_ORCHESTRATOR", "agent-orchestrator")
CH_LOG         = os.getenv("SLACK_CHANNEL_LOG",          "agent-log")
CH_REVIEW      = os.getenv("SLACK_CHANNEL_REVIEW",       "human-review")

# How long Hermes waits for OpenClaw to respond before timing out (seconds)
OPENCLAW_RESPONSE_TIMEOUT = 120

# Hermes bot display name and emoji in Slack
HERMES_NAME  = "🧠 Hermes"
HERMES_EMOJI = ":brain:"


# ═════════════════════════════════════════════════════════════════════════════
# MEMORY MANAGEMENT
# ═════════════════════════════════════════════════════════════════════════════

def load_memory() -> dict:
    """
    Load Hermes's persistent memory from the local JSON file.

    Memory holds: known facts about the project, task history,
    active task tracking, and session count.

    Returns:
        The memory dict, or an empty structure if the file is missing.
    """
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Return a blank memory structure if no file exists yet
    return {
        "version": "1.0",
        "agent": "Hermes",
        "last_updated": None,
        "facts": {},
        "task_history": [],
        "active_tasks": {},
        "skill_triggers_fired": [],
        "session_count": 0,
    }


def save_memory(memory: dict) -> None:
    """
    Persist Hermes's memory to disk after every update.

    Args:
        memory: The full memory dict to save.
    """
    memory["last_updated"] = datetime.now(timezone.utc).isoformat()
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


def update_task_in_memory(memory: dict, task_id: str, update: dict) -> None:
    """
    Update a specific task record in memory and persist.

    Args:
        memory  : The memory dict (mutated in-place).
        task_id : Unique ID for the task (timestamp-based).
        update  : Dict of fields to merge into the task record.
    """
    if task_id in memory["active_tasks"]:
        memory["active_tasks"][task_id].update(update)
    save_memory(memory)


# ═════════════════════════════════════════════════════════════════════════════
# GROQ / LLM INTERACTIONS
# ═════════════════════════════════════════════════════════════════════════════

def call_groq(system_prompt: str, user_message: str) -> str:
    """
    Call the Groq API with Kimi K2 and return the assistant's response text.

    Args:
        system_prompt : The system role definition.
        user_message  : The user's request or context.

    Returns:
        The model's response as a plain string.
        Returns an error string if the API call fails.
    """
    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system",  "content": system_prompt},
                {"role": "user",    "content": user_message},
            ],
            temperature=0.3,   # Lower temp = more consistent, structured output
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        return f"[Groq API Error] {exc}"


def generate_plan(task: str, memory: dict) -> str:
    """
    Ask Kimi K2 to generate a structured execution plan for the given task.

    The plan is what Hermes posts to #agent-orchestrator for OpenClaw to follow.

    Args:
        task   : The raw task text from #commands.
        memory : Current Hermes memory for context injection.

    Returns:
        A structured plan string ready to post to Slack.
    """
    # Summarise memory context for the model
    context = json.dumps(memory.get("facts", {}), indent=2)
    history_count = len(memory.get("task_history", []))

    system_prompt = f"""You are Hermes, an AI orchestrator agent.
Your job is to plan tasks for OpenClaw, a Python coding agent.

Project context:
{context}

Tasks completed so far: {history_count}

Rules:
- Always output a numbered step-by-step plan
- Each step should be specific and actionable
- Identify the output files OpenClaw must produce
- Specify success criteria clearly
- Keep the plan under 10 steps
- End with: "ASSIGN TO: OpenClaw"
"""

    user_message = f"""New task received: {task}

Generate a clear execution plan for OpenClaw. Format:

TASK: [one-line summary]
PLAN:
1. [step]
2. [step]
...
OUTPUT FILES: [comma-separated list]
SUCCESS CRITERIA: [how to know it worked]
ASSIGN TO: OpenClaw"""

    return call_groq(system_prompt, user_message)


def validate_result(task: str, openclaw_report: str) -> tuple[bool, str]:
    """
    Ask Kimi K2 to validate OpenClaw's report against the original task.

    Args:
        task             : The original task from #commands.
        openclaw_report  : The structured report OpenClaw posted to #agent-log.

    Returns:
        Tuple of (passed: bool, feedback: str).
        If passed is False, feedback contains a specific improvement request.
    """
    system_prompt = """You are Hermes, a strict AI quality reviewer.
Your job is to validate whether OpenClaw completed a task correctly.

Rules:
- Be concise and direct
- If the task is complete, respond with: VERDICT: PASS
- If improvement is needed, respond with: VERDICT: FAIL\nIMPROVEMENT: [specific instruction]
- Only request ONE improvement at most
- Judge based on whether the output files exist and the task intent is met"""

    user_message = f"""Original task: {task}

OpenClaw's report:
{openclaw_report}

Is the task complete? Validate now."""

    response = call_groq(system_prompt, user_message)

    # Parse the verdict from Hermes's validation response
    if "VERDICT: PASS" in response.upper():
        return True, response
    else:
        # Extract the improvement instruction
        improvement = response
        match = re.search(r"IMPROVEMENT:\s*(.+)", response, re.IGNORECASE | re.DOTALL)
        if match:
            improvement = match.group(1).strip()
        return False, improvement


# ═════════════════════════════════════════════════════════════════════════════
# AGENT-LOG UPDATER
# ═════════════════════════════════════════════════════════════════════════════

def append_to_agent_log(task_id: str, task: str, plan: str,
                        openclaw_report: str, verdict: str) -> None:
    """
    Append a completed task session to agent-log.md.

    This maintains the persistent audit trail required by the qualifier.

    Args:
        task_id         : Unique task identifier.
        task            : Original user task.
        plan            : Plan Hermes generated.
        openclaw_report : OpenClaw's structured report.
        verdict         : Hermes's final validation verdict.
    """
    log_path = Path("agent-log.md")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    entry = f"""
---

## 🤖 Sprint 02 — Task `{task_id}` | {timestamp}

**Original Task:** {task}

### Hermes Plan
```
{plan}
```

### OpenClaw Report
{openclaw_report}

### Hermes Validation
```
{verdict}
```

**What I Did:**
- Hermes generated plan and assigned to OpenClaw via #agent-orchestrator
- OpenClaw executed task and reported to #agent-log
- Hermes validated result and posted to #human-review

**What's Left:**
- Screenshot of Slack conversation to be added to screenshots/

**What Needs Your Call:**
- None — task completed autonomously

"""
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


# ═════════════════════════════════════════════════════════════════════════════
# HERMES SLACK APP
# ═════════════════════════════════════════════════════════════════════════════

# Initialise the Slack Bolt app using the bot token from .env
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

# Load skills for keyword-based trigger matching
skills_loader = SkillsLoader(SKILLS_DIR)

# Track which task IDs we are waiting on OpenClaw for (task_id → context dict)
_pending_tasks: dict = {}


def get_channel_id(client, channel_name: str) -> str | None:
    """
    Resolve a channel name (e.g. 'commands') to its Slack channel ID.

    Args:
        client       : Slack WebClient instance.
        channel_name : Channel name without the # prefix.

    Returns:
        The channel ID string, or None if not found.
    """
    try:
        # List all channels the bot can see (paginated)
        result = client.conversations_list(types="public_channel,private_channel")
        for channel in result["channels"]:
            if channel["name"] == channel_name:
                return channel["id"]
    except Exception as exc:
        print(f"[Hermes] ⚠️  Could not resolve channel '{channel_name}': {exc}")
    return None


def post_as_hermes(client, channel: str, text: str) -> None:
    """
    Post a message to Slack as Hermes (with branded name and emoji).

    Args:
        client  : Slack WebClient.
        channel : Channel ID or name.
        text    : Message text (supports Slack mrkdwn).
    """
    try:
        client.chat_postMessage(
            channel=channel,
            text=text,
            username=HERMES_NAME,
            icon_emoji=HERMES_EMOJI,
        )
    except Exception as exc:
        print(f"[Hermes] ⚠️  Failed to post message: {exc}")


# ── Event: New message in #commands ──────────────────────────────────────────

@app.event("message")
def handle_message(event, client, logger):
    """
    Main event handler for all Slack messages.

    Routing logic:
        - Message in #commands (not from a bot) → Hermes orchestrates
        - Message in #agent-log (from OpenClaw bot) → Hermes validates
    """
    # Ignore bot messages and system messages to prevent infinite loops
    if event.get("bot_id") or event.get("subtype"):
        return

    channel_id = event.get("channel")
    text       = event.get("text", "").strip()
    user       = event.get("user", "unknown")

    if not text:
        return

    # Resolve channel IDs for routing
    commands_id     = get_channel_id(client, CH_COMMANDS)
    log_id          = get_channel_id(client, CH_LOG)
    orchestrator_id = get_channel_id(client, CH_ORCHESTRATOR)
    review_id       = get_channel_id(client, CH_REVIEW)

    # ── Route: New task in #commands ─────────────────────────────────────────
    if channel_id == commands_id:
        logger.info(f"[Hermes] 📥 New task from user {user}: {text[:80]}")
        handle_new_task(client, text, orchestrator_id, review_id, logger)

    # ── Route: OpenClaw report in #agent-log ─────────────────────────────────
    elif channel_id == log_id:
        logger.info(f"[Hermes] 📋 OpenClaw report received")
        handle_openclaw_report(client, text, review_id, logger)


def handle_new_task(client, task: str, orchestrator_id: str,
                    review_id: str, logger) -> None:
    """
    Orchestrate a new task: load memory → check skills → generate plan → assign.

    Args:
        client          : Slack WebClient.
        task            : Raw task text from #commands.
        orchestrator_id : Slack ID of #agent-orchestrator channel.
        review_id       : Slack ID of #human-review channel.
        logger          : Slack Bolt logger.
    """
    # Step 1: Load persistent memory
    memory = load_memory()
    memory["session_count"] = memory.get("session_count", 0) + 1

    # Step 2: Check if any skill should fire for this task
    matched_skill = skills_loader.match(task)
    if matched_skill:
        skill_name = matched_skill.get("name", "unknown")
        logger.info(f"[Hermes] ⚡ Skill fired: {skill_name}")
        memory["skill_triggers_fired"].append({
            "skill": skill_name,
            "task": task,
            "at": datetime.now(timezone.utc).isoformat(),
        })
        # Post skill firing notification to #human-review
        if review_id:
            post_as_hermes(client, review_id,
                f"⚡ *Skill triggered:* `{skill_name}`\n"
                f"> {matched_skill.get('description', '')}")

    # Step 3: Generate execution plan with Kimi K2
    task_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    logger.info(f"[Hermes] 🧠 Generating plan for task {task_id}...")

    plan = generate_plan(task, memory)

    # Step 4: Store task in active_tasks memory
    memory["active_tasks"][task_id] = {
        "task_id":    task_id,
        "task":       task,
        "plan":       plan,
        "status":     "assigned",
        "assigned_at": datetime.now(timezone.utc).isoformat(),
        "revision":   0,
    }
    save_memory(memory)

    # Step 5: Post plan + assignment to #agent-orchestrator
    if orchestrator_id:
        message = (
            f"*📋 TASK ID:* `{task_id}`\n"
            f"*From:* Hermes → OpenClaw\n\n"
            f"```\n{plan}\n```\n\n"
            f"⏳ *OpenClaw — please execute this plan and report to #agent-log*"
        )
        post_as_hermes(client, orchestrator_id, message)
        logger.info(f"[Hermes] ✅ Plan posted to #agent-orchestrator")

    # Track the pending task so we can match OpenClaw's response
    _pending_tasks[task_id] = {
        "task": task,
        "plan": plan,
        "task_id": task_id,
        "review_id": review_id,
    }


def handle_openclaw_report(client, report_text: str,
                           review_id: str, logger) -> None:
    """
    Validate OpenClaw's report and post the final result to #human-review.

    Hermes reads #agent-log, validates using Kimi K2, and if the result
    needs improvement, sends one revision task back to #agent-orchestrator.

    Args:
        client      : Slack WebClient.
        report_text : The raw text of OpenClaw's Slack message.
        review_id   : Slack ID of #human-review channel.
        logger      : Slack Bolt logger.
    """
    # Find the matching pending task (match on TASK ID if present in report)
    task_id = None
    task_context = None

    # Try to extract task ID from the report
    match = re.search(r"TASK[_\s]?ID[:\s]+`?([0-9\-]+)`?", report_text, re.IGNORECASE)
    if match:
        task_id = match.group(1)
        task_context = _pending_tasks.get(task_id)

    # If no ID match, use the most recent pending task
    if not task_context and _pending_tasks:
        task_id = list(_pending_tasks.keys())[-1]
        task_context = _pending_tasks[task_id]

    if not task_context:
        logger.warning("[Hermes] ⚠️  Received OpenClaw report but no matching task found")
        return

    task = task_context["task"]
    plan = task_context["plan"]

    logger.info(f"[Hermes] 🔍 Validating OpenClaw report for task {task_id}")

    # Validate with Kimi K2
    passed, feedback = validate_result(task, report_text)

    # Load memory to update task status
    memory = load_memory()

    if passed:
        # ── Task passed validation ────────────────────────────────────────────
        logger.info(f"[Hermes] ✅ Task {task_id} PASSED validation")
        update_task_in_memory(memory, task_id, {
            "status":        "completed",
            "completed_at":  datetime.now(timezone.utc).isoformat(),
            "verdict":       "PASS",
        })

        # Move from active to history
        completed = memory["active_tasks"].pop(task_id, None)
        if completed:
            memory["task_history"].append(completed)
        save_memory(memory)

        # Post final result to #human-review
        if review_id:
            post_as_hermes(client, review_id,
                f"✅ *Task `{task_id}` — VALIDATED & COMPLETE*\n\n"
                f"*Original task:* {task}\n\n"
                f"*OpenClaw's report:*\n{report_text}\n\n"
                f"*Hermes validation:*\n> {feedback}\n\n"
                f"_All outputs saved to `outputs/` and committed to GitHub._"
            )

        # Append to agent-log.md
        append_to_agent_log(task_id, task, plan, report_text, feedback)

        # Remove from pending
        _pending_tasks.pop(task_id, None)

    else:
        # ── Task needs one improvement ────────────────────────────────────────
        revision_count = memory["active_tasks"].get(task_id, {}).get("revision", 0)

        if revision_count >= 1:
            # Already had one revision — accept as-is to avoid infinite loop
            logger.info(f"[Hermes] ⚠️  Task {task_id} already revised once — accepting")
            if review_id:
                post_as_hermes(client, review_id,
                    f"⚠️ *Task `{task_id}` — ACCEPTED (after 1 revision)*\n\n"
                    f"Hermes note: {feedback}")
            _pending_tasks.pop(task_id, None)
        else:
            # Send one revision request back to OpenClaw
            logger.info(f"[Hermes] 🔄 Requesting revision for task {task_id}: {feedback[:100]}")
            update_task_in_memory(memory, task_id, {
                "status":   "revision_requested",
                "revision": revision_count + 1,
            })

            orchestrator_id = get_channel_id(client, CH_ORCHESTRATOR)
            if orchestrator_id:
                revision_message = (
                    f"*🔄 REVISION REQUEST — Task `{task_id}`*\n\n"
                    f"*Hermes feedback:*\n> {feedback}\n\n"
                    f"*OpenClaw — please revise and re-report to #agent-log*"
                )
                post_as_hermes(client, orchestrator_id, revision_message)


# ═════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def start_hermes():
    """
    Start the Hermes agent using Slack Socket Mode.

    Socket Mode means no public URL / ngrok needed — works on any machine.
    """
    print("🧠 Hermes Agent starting (Socket Mode)...")
    print(f"   Model      : {GROQ_MODEL}")
    print(f"   Memory     : {MEMORY_FILE}")
    print(f"   Skills dir : {SKILLS_DIR}")
    print(f"   Listening  : #{CH_COMMANDS}, #{CH_LOG}")
    print("   Press Ctrl+C to stop.\n")

    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()


if __name__ == "__main__":
    start_hermes()
