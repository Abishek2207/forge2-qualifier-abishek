"""
agents/hermes.py — FINAL DEBUG + MESSAGE + APP_MENTION VERSION
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from threading import Lock

load_dotenv()

from groq import Groq
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
MEMORY_FILE = Path("memory/hermes_memory.json")

CH_ORCHESTRATOR = os.getenv("SLACK_CHANNEL_ORCHESTRATOR", "agent-orchestrator")
CH_REVIEW = os.getenv("SLACK_CHANNEL_REVIEW", "human-review")

HERMES_NAME = "🧠 Hermes"
HERMES_EMOJI = ":brain:"

_pending_tasks = {}
_lock = Lock()

app = App(token=os.getenv("SLACK_BOT_TOKEN"))


def load_memory():
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    return {"task_history": [], "active_tasks": {}, "facts": {}}


def save_memory(memory):
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    memory["last_updated"] = datetime.now(timezone.utc).isoformat()
    MEMORY_FILE.write_text(json.dumps(memory, indent=2), encoding="utf-8")


def get_groq():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


def call_groq(system, user):
    client = get_groq()
    res = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        max_tokens=1200,
    )
    return res.choices[0].message.content


def post(client, channel, text):
    try:
        client.chat_postMessage(
            channel=channel,
            text=text,
            username=HERMES_NAME,
            icon_emoji=HERMES_EMOJI,
        )
    except Exception as e:
        print("[Hermes Slack error]", e)


def generate_plan(task):
    system = """
You are Hermes Orchestrator.
Create step-by-step plan max 8 steps.
Include output file.
End with ASSIGN TO OPENCLAW.
"""
    return call_groq(system, f"TASK: {task}")


def validate(task, report):
    system = """
Return ONLY PASS or FAIL + IMPROVEMENT.
Only one improvement max.
"""
    res = call_groq(system, f"{task}\n{report}")
    return ("PASS" in res.upper()), res


def is_command(text: str) -> bool:
    text = text.lower()
    return (
        "#commands" in text
        or "create" in text
        or text.startswith("hello")
        or text.startswith("hi")
        or "forge 2" in text
    )


def is_log(text: str) -> bool:
    text = text.lower()
    return "#agent-log" in text or "openclaw report" in text


def handle_task(event, client):
    print("🔥 EVENT RECEIVED:", event)

    if event.get("bot_id") or event.get("subtype"):
        return

    text = event.get("text", "")
    if not text:
        return

    if is_command(text):
        memory = load_memory()
        task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        plan = generate_plan(text)

        with _lock:
            _pending_tasks[task_id] = {"task": text, "plan": plan}

        save_memory(memory)

        post(
            client,
            CH_ORCHESTRATOR,
            f"📌 TASK {task_id}\n\n{plan}\n\n→ OpenClaw",
        )

        print(f"[Hermes] Task created: {task_id}")

    elif is_log(text):
        if not _pending_tasks:
            return

        task_id = list(_pending_tasks.keys())[-1]
        data = _pending_tasks[task_id]

        passed, result = validate(data["task"], text)

        if passed:
            post(client, CH_REVIEW, f"✅ TASK {task_id} PASSED\n\n{text}")
        else:
            post(client, CH_ORCHESTRATOR, f"🔄 TASK {task_id} REVISION\n\n{result}")


@app.event("message")
def message_handler(event, client, logger):
    handle_task(event, client)


@app.event("app_mention")
def mention_handler(event, client, logger):
    handle_task(event, client)


def start_hermes():
    print("🧠 Hermes starting...")
    print("Listening on Slack...")
    print("Test with: @Demo App hello OR #commands hello")

    token = os.getenv("SLACK_APP_TOKEN")

    if not token:
        print("❌ Missing SLACK_APP_TOKEN")
        return

    SocketModeHandler(app, token).start()


if __name__ == "__main__":
    start_hermes()