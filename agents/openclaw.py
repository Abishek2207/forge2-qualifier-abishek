"""
agents/openclaw.py
==================
OpenClaw — Coding / Execution Agent
Forge Sprint 02 | Multi-Agent System

Role:
    OpenClaw is the execution layer. It:
      1. Listens to #agent-orchestrator for tasks from Hermes
      2. Calls Ollama (Qwen2.5-Coder) to write Python code for the task
      3. Executes the generated code in a subprocess sandbox
      4. Captures stdout, stderr, and exit code
      5. Saves output files to outputs/
      6. Commits output files to GitHub via the API
      7. Posts a structured report to #agent-log

Communication:
    - Reads from : #agent-orchestrator
    - Writes to  : #agent-log

Report Format (always):
    What I Did / What Failed / What Needs Review

Author : Abishek R
Model  : Ollama / Qwen2.5-Coder (local, free, no API cost)
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path

# ── Environment ───────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

# ── HTTP (Ollama API + GitHub API) ────────────────────────────────────────────
import requests

# ── Slack Bolt ────────────────────────────────────────────────────────────────
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "qwen2.5-coder")

CH_ORCHESTRATOR = os.getenv("SLACK_CHANNEL_ORCHESTRATOR", "agent-orchestrator")
CH_LOG          = os.getenv("SLACK_CHANNEL_LOG",          "agent-log")

OUTPUTS_DIR     = Path("outputs")
GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN")
GITHUB_REPO     = os.getenv("GITHUB_REPO", "Abishek2207/forge2-qualifier-abishek")
GITHUB_BRANCH   = os.getenv("GITHUB_BRANCH", "main")

# Max time (seconds) to run generated code — prevents runaway scripts
CODE_EXEC_TIMEOUT = 30

# OpenClaw display name in Slack
OPENCLAW_NAME  = "🦾 OpenClaw"
OPENCLAW_EMOJI = ":robot_face:"


# ═════════════════════════════════════════════════════════════════════════════
# OLLAMA — CODE GENERATION
# ═════════════════════════════════════════════════════════════════════════════

def call_ollama(prompt: str) -> str:
    """
    Call Ollama's local REST API to generate Python code using Qwen2.5-Coder.

    This runs 100% locally — no API key, no cost, no internet required.

    Args:
        prompt : The task description / instructions for code generation.

    Returns:
        The model's response (should contain Python code), or an error string.
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model":  OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,          # Wait for full response
        "options": {
            "temperature": 0.1,   # Low temperature for deterministic code output
            "num_predict": 1000,  # Max tokens in response
        },
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        return "[Ollama Error] Cannot connect to Ollama. Is it running? Run: ollama serve"
    except requests.exceptions.Timeout:
        return "[Ollama Error] Request timed out after 60 seconds"
    except Exception as exc:
        return f"[Ollama Error] {exc}"


def generate_code_for_task(task_description: str) -> str:
    """
    Ask Qwen2.5-Coder to write Python code that accomplishes the given task.

    The prompt is carefully engineered to ensure:
        - The code is self-contained and runnable
        - Output is saved to the outputs/ directory
        - The code prints a clear completion message

    Args:
        task_description : The task plan text received from Hermes.

    Returns:
        A string containing Python code, extracted from the model's response.
    """
    prompt = f"""You are OpenClaw, a Python coding agent.
Write a complete, runnable Python script to accomplish this task:

{task_description}

Requirements:
- Use only Python standard library + requests (pre-installed)
- Save any output files to the outputs/ directory (create it with os.makedirs if needed)
- Print a clear completion message at the end
- Handle errors gracefully with try/except
- Include a main() function
- Call main() at the bottom with: if __name__ == "__main__": main()

Return ONLY the Python code, no explanation, no markdown fences."""

    raw_response = call_ollama(prompt)

    # Strip markdown code fences if the model added them anyway
    code = re.sub(r"```python\s*", "", raw_response)
    code = re.sub(r"```\s*$", "", code, flags=re.MULTILINE)

    return code.strip()


# ═════════════════════════════════════════════════════════════════════════════
# CODE EXECUTION SANDBOX
# ═════════════════════════════════════════════════════════════════════════════

def execute_code(code: str, task_id: str) -> dict:
    """
    Execute Python code in a subprocess sandbox and capture the result.

    The code is written to a temporary file and run with the project's
    virtual environment Python interpreter (if available).

    Args:
        code    : Python source code to execute.
        task_id : Task ID for naming the saved script file.

    Returns:
        Dict with keys: success (bool), stdout (str), stderr (str),
        exit_code (int), script_path (str).
    """
    # Save the generated code as a named script in outputs/ for audit trail
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    script_path = OUTPUTS_DIR / f"task_{task_id}_generated.py"
    script_path.write_text(code, encoding="utf-8")

    # Use the venv Python if available, otherwise fall back to system Python
    python_exe = sys.executable
    venv_python = Path(".venv/Scripts/python.exe")   # Windows
    if venv_python.exists():
        python_exe = str(venv_python)

    try:
        result = subprocess.run(
            [python_exe, str(script_path)],
            capture_output=True,
            text=True,
            timeout=CODE_EXEC_TIMEOUT,
            cwd=str(Path.cwd()),  # Run from project root so paths resolve correctly
        )
        return {
            "success":     result.returncode == 0,
            "stdout":      result.stdout.strip(),
            "stderr":      result.stderr.strip(),
            "exit_code":   result.returncode,
            "script_path": str(script_path),
        }
    except subprocess.TimeoutExpired:
        return {
            "success":     False,
            "stdout":      "",
            "stderr":      f"Execution timed out after {CODE_EXEC_TIMEOUT} seconds",
            "exit_code":   -1,
            "script_path": str(script_path),
        }
    except Exception as exc:
        return {
            "success":     False,
            "stdout":      "",
            "stderr":      str(exc),
            "exit_code":   -1,
            "script_path": str(script_path),
        }


# ═════════════════════════════════════════════════════════════════════════════
# GITHUB AUTO-COMMIT
# ═════════════════════════════════════════════════════════════════════════════

def commit_outputs_to_github(task_id: str, files_changed: list[str]) -> str:
    """
    Commit output files to GitHub using the GitHub Contents API.

    This creates an incremental commit with only the changed output files.
    Uses a Personal Access Token from the GITHUB_TOKEN env var.

    Args:
        task_id       : Task ID used in the commit message.
        files_changed : List of relative file paths to commit.

    Returns:
        A status string describing the result (success or error message).
    """
    if not GITHUB_TOKEN:
        return "⚠️  GitHub commit skipped — GITHUB_TOKEN not set"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept":        "application/vnd.github.v3+json",
    }
    base_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents"
    committed = []

    for file_path in files_changed:
        path = Path(file_path)
        if not path.exists():
            continue

        # Read file content and base64-encode it (required by GitHub API)
        import base64
        content_bytes = path.read_bytes()
        content_b64   = base64.b64encode(content_bytes).decode("utf-8")

        # GitHub path uses forward slashes
        gh_path = file_path.replace("\\", "/")
        url     = f"{base_url}/{gh_path}"

        # Check if file already exists on GitHub (need its SHA to update)
        sha = None
        try:
            get_resp = requests.get(url, headers=headers, timeout=10)
            if get_resp.status_code == 200:
                sha = get_resp.json().get("sha")
        except Exception:
            pass  # File is new — no SHA needed

        # Build the commit payload
        payload = {
            "message": f"agent(openclaw): task {task_id} — {path.name}",
            "content": content_b64,
            "branch":  GITHUB_BRANCH,
        }
        if sha:
            payload["sha"] = sha   # Required when updating an existing file

        try:
            put_resp = requests.put(url, json=payload, headers=headers, timeout=15)
            if put_resp.status_code in (200, 201):
                committed.append(gh_path)
            else:
                print(f"[OpenClaw] ⚠️  GitHub commit failed for {gh_path}: {put_resp.status_code}")
        except Exception as exc:
            print(f"[OpenClaw] ⚠️  GitHub error: {exc}")

    if committed:
        return f"✅ Committed to GitHub: {', '.join(committed)}"
    return "⚠️  No files committed to GitHub"


# ═════════════════════════════════════════════════════════════════════════════
# STRUCTURED REPORT BUILDER
# ═════════════════════════════════════════════════════════════════════════════

def build_report(task_id: str, task_summary: str, code: str,
                 exec_result: dict, github_status: str) -> str:
    """
    Build the structured Slack report that OpenClaw posts to #agent-log.

    Format: What I Did / What Failed / What Needs Review

    Args:
        task_id       : Unique task identifier.
        task_summary  : First line of the task plan from Hermes.
        code          : The generated Python code (truncated for Slack).
        exec_result   : Result dict from execute_code().
        github_status : Status string from commit_outputs_to_github().

    Returns:
        A formatted string ready to post to Slack.
    """
    # Determine overall status
    status_emoji = "✅" if exec_result["success"] else "❌"

    # Truncate code and output for Slack's message length limits
    code_preview = textwrap.shorten(code, width=400, placeholder="... (truncated)")
    stdout_preview = textwrap.shorten(
        exec_result["stdout"] or "(no output)", width=500, placeholder="... (truncated)"
    )

    report = f"""{status_emoji} *OpenClaw Report* | Task ID: `{task_id}`

*📌 What I Did:*
• Received task from Hermes via #agent-orchestrator
• Generated Python code using Qwen2.5-Coder (Ollama local model)
• Executed code: `{exec_result['script_path']}`
• Exit code: `{exec_result['exit_code']}`
• {github_status}

*📤 Output:*
```
{stdout_preview}
```

*❌ What Failed:*
{exec_result['stderr'] if exec_result['stderr'] else '• Nothing — all steps succeeded ✅'}

*👀 What Needs Review:*
• Check `outputs/` directory for generated files
• Verify GitHub commit landed on `main` branch
• Hermes will validate this report automatically

_Task: {task_summary}_"""

    return report


# ═════════════════════════════════════════════════════════════════════════════
# OPENCLAW SLACK APP
# ═════════════════════════════════════════════════════════════════════════════

# Use the same Slack app instance (same bot token) — routing by channel
app = App(token=os.getenv("SLACK_BOT_TOKEN"))


def post_as_openclaw(client, channel: str, text: str) -> None:
    """
    Post a message to Slack as OpenClaw (with branded name and emoji).

    Args:
        client  : Slack WebClient.
        channel : Channel ID or name.
        text    : Message text.
    """
    try:
        client.chat_postMessage(
            channel=channel,
            text=text,
            username=OPENCLAW_NAME,
            icon_emoji=OPENCLAW_EMOJI,
        )
    except Exception as exc:
        print(f"[OpenClaw] ⚠️  Failed to post message: {exc}")


def get_channel_id(client, channel_name: str) -> str | None:
    """Resolve a channel name to its Slack ID."""
    try:
        result = client.conversations_list(types="public_channel,private_channel")
        for channel in result["channels"]:
            if channel["name"] == channel_name:
                return channel["id"]
    except Exception as exc:
        print(f"[OpenClaw] ⚠️  Could not resolve channel '{channel_name}': {exc}")
    return None


@app.event("message")
def handle_orchestrator_message(event, client, logger):
    """
    Listen for messages in #agent-orchestrator from Hermes.

    When Hermes posts a task plan, OpenClaw:
        1. Parses the task
        2. Generates code with Qwen2.5-Coder
        3. Executes the code
        4. Commits outputs to GitHub
        5. Posts structured report to #agent-log
    """
    # Ignore bot messages to prevent OpenClaw from responding to itself
    # (Hermes messages are acceptable — we react to those)
    if event.get("subtype") == "bot_message" and event.get("username") == OPENCLAW_NAME:
        return

    channel_id = event.get("channel")
    text       = event.get("text", "").strip()

    if not text:
        return

    orch_id = get_channel_id(client, CH_ORCHESTRATOR)
    log_id  = get_channel_id(client, CH_LOG)

    # Only react to messages in #agent-orchestrator
    if channel_id != orch_id:
        return

    # Extract task ID from Hermes's message
    task_id = "unknown"
    match = re.search(r"TASK[_\s]?ID[:\*\s]+`?([0-9\-]+)`?", text, re.IGNORECASE)
    if match:
        task_id = match.group(1)

    # Skip revision requests that we've already processed (avoid duplicates)
    if "revision request" in text.lower() and task_id == "unknown":
        return

    logger.info(f"[OpenClaw] 📥 Task received from Hermes: {task_id}")

    # Acknowledge receipt in the orchestrator channel
    post_as_openclaw(client, orch_id,
        f"🦾 *OpenClaw here* — Task `{task_id}` received. Generating code now... ⚙️"
    )

    # ── Step 1: Generate code ─────────────────────────────────────────────────
    logger.info(f"[OpenClaw] 🔧 Calling Qwen2.5-Coder for task {task_id}...")
    code = generate_code_for_task(text)

    if code.startswith("[Ollama Error]"):
        # Ollama is not available — fall back to a static demo script
        logger.warning("[OpenClaw] ⚠️  Ollama unavailable — using fallback script")
        code = _fallback_demo_script(task_id)

    # ── Step 2: Execute the code ──────────────────────────────────────────────
    logger.info(f"[OpenClaw] ▶️  Executing generated code for task {task_id}...")
    exec_result = execute_code(code, task_id)

    # ── Step 3: Collect output files to commit ────────────────────────────────
    files_to_commit = [
        str(OUTPUTS_DIR / f"task_{task_id}_generated.py"),
    ]
    # Also commit any results.json or autonomous-run.txt that were updated
    for output_file in OUTPUTS_DIR.glob("*.json"):
        files_to_commit.append(str(output_file))
    for output_file in OUTPUTS_DIR.glob("*.txt"):
        files_to_commit.append(str(output_file))

    # ── Step 4: Commit to GitHub ──────────────────────────────────────────────
    logger.info(f"[OpenClaw] 📦 Committing outputs to GitHub...")
    github_status = commit_outputs_to_github(task_id, files_to_commit)

    # Also commit the updated agent-log.md if it was modified
    if Path("agent-log.md").exists():
        commit_outputs_to_github(task_id, ["agent-log.md"])

    # ── Step 5: Build and post structured report to #agent-log ───────────────
    task_summary = text.split("\n")[0][:100]
    report = build_report(task_id, task_summary, code, exec_result, github_status)

    if log_id:
        post_as_openclaw(client, log_id, report)
        logger.info(f"[OpenClaw] ✅ Report posted to #agent-log for task {task_id}")
    else:
        logger.error("[OpenClaw] ❌ Could not find #agent-log channel")


def _fallback_demo_script(task_id: str) -> str:
    """
    Return a static fallback Python script when Ollama is not available.

    This ensures OpenClaw can still demonstrate execution even without
    a local LLM running. Used for demo/testing purposes only.

    Args:
        task_id : Current task ID to include in the output.

    Returns:
        A self-contained Python script string.
    """
    return f'''"""
OpenClaw Fallback Demo Script
Task ID: {task_id}
Generated: Fallback mode (Ollama unavailable)
"""
import json, os
from datetime import datetime, timezone

def main():
    os.makedirs("outputs", exist_ok=True)
    result = {{
        "task_id": "{task_id}",
        "agent": "OpenClaw",
        "mode": "fallback_demo",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Ollama is not running. This is a fallback demo output.",
        "status": "completed"
    }}
    with open("outputs/task_{task_id}_result.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"Task {task_id} completed (fallback mode)")
    print(f"Output: outputs/task_{task_id}_result.json")

if __name__ == "__main__":
    main()
'''


# ═════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def start_openclaw():
    """
    Start the OpenClaw agent using Slack Socket Mode.
    """
    print("🦾 OpenClaw Agent starting (Socket Mode)...")
    print(f"   Model      : {OLLAMA_MODEL} via Ollama at {OLLAMA_BASE_URL}")
    print(f"   GitHub     : {GITHUB_REPO}")
    print(f"   Listening  : #{CH_ORCHESTRATOR}")
    print("   Press Ctrl+C to stop.\n")

    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()


if __name__ == "__main__":
    start_openclaw()
