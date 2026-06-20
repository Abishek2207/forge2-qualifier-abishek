"""
run_system.py
=============
System Launcher — Forge Sprint 02 Multi-Agent System

Starts both Hermes and OpenClaw agents in separate threads so they both
listen on Slack simultaneously using the same Slack App (Socket Mode).

Usage:
    python run_system.py           → Start both agents
    python run_system.py --hermes  → Start Hermes only
    python run_system.py --openclaw → Start OpenClaw only
    python run_system.py --demo    → Run a local demo (no Slack needed)

Author : Abishek R
"""

import argparse
import os
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# Load .env before importing anything that uses env vars
from dotenv import load_dotenv
load_dotenv()


# ═════════════════════════════════════════════════════════════════════════════
# PRE-FLIGHT CHECKS
# ═════════════════════════════════════════════════════════════════════════════

def check_environment() -> list[str]:
    """
    Validate that all required environment variables are set.

    Returns:
        List of missing variable names (empty list = all good).
    """
    required = [
        "SLACK_BOT_TOKEN",
        "SLACK_APP_TOKEN",
        "GROQ_API_KEY",
    ]
    missing = [var for var in required if not os.getenv(var)]
    return missing


def print_banner() -> None:
    """Print the startup banner with system info."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         FORGE SPRINT 02 — MULTI-AGENT SYSTEM                 ║
║         Hermes (Orchestrator) + OpenClaw (Coding)            ║
╠══════════════════════════════════════════════════════════════╣
║  Author    : Abishek R                                       ║
║  Repo      : Abishek2207/forge2-qualifier-abishek            ║
║  Hermes    : Groq / Kimi K2      (reasoning + planning)      ║
║  OpenClaw  : Ollama / Qwen2.5    (code generation)           ║
║  Comms     : Slack (Socket Mode — no public URL needed)      ║
╚══════════════════════════════════════════════════════════════╝
""")


def check_ollama() -> bool:
    """
    Check if Ollama is running locally.

    Returns:
        True if Ollama is reachable, False otherwise.
    """
    try:
        import requests
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        resp = requests.get(f"{base_url}/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


# ═════════════════════════════════════════════════════════════════════════════
# DEMO MODE (no Slack required)
# ═════════════════════════════════════════════════════════════════════════════

def run_demo() -> None:
    """
    Run a local demo of the agent workflow without requiring Slack.

    Simulates the full pipeline:
        1. User task input
        2. Hermes generates plan (Groq)
        3. OpenClaw generates & executes code (Ollama or fallback)
        4. Outputs saved to outputs/
        5. Summary report printed

    This is useful for testing the agents without a Slack workspace configured.
    """
    print("\n🎬 DEMO MODE — No Slack required")
    print("=" * 60)

    # ── Simulate Hermes planning ──────────────────────────────────────────────
    from agents.hermes import generate_plan, validate_result, load_memory

    task = "Fetch the titles from python.org, github.com, and groq.com. Save results to outputs/demo_results.json"
    print(f"\n📥 User task: {task}\n")

    print("🧠 Hermes generating plan (Groq / Kimi K2)...")
    memory = load_memory()
    plan = generate_plan(task, memory)
    print(f"\n📋 Hermes Plan:\n{plan}\n")

    # ── Simulate OpenClaw execution ───────────────────────────────────────────
    from agents.openclaw import generate_code_for_task, execute_code, build_report, commit_outputs_to_github

    task_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    print(f"🦾 OpenClaw generating code for task {task_id}...")

    code = generate_code_for_task(plan)
    print(f"\n📜 Generated code preview:\n{code[:400]}...\n")

    print("▶️  Executing code...")
    exec_result = execute_code(code, task_id)
    print(f"\n📤 Output:\n{exec_result['stdout']}")

    if exec_result['stderr']:
        print(f"⚠️  Errors:\n{exec_result['stderr']}")

    # ── GitHub commit ─────────────────────────────────────────────────────────
    from pathlib import Path
    outputs = Path("outputs")
    files = [str(f) for f in outputs.glob("*") if f.is_file()]
    print(f"\n📦 Committing {len(files)} file(s) to GitHub...")
    gh_status = commit_outputs_to_github(task_id, files)
    print(f"   {gh_status}")

    # ── Hermes validation ─────────────────────────────────────────────────────
    report = build_report(task_id, task[:100], code, exec_result, gh_status)
    print(f"\n🔍 Hermes validating result...")
    passed, feedback = validate_result(task, report)

    print(f"\n{'✅ PASS' if passed else '❌ NEEDS REVISION'}")
    print(f"Feedback: {feedback[:300]}")

    print("\n" + "=" * 60)
    print("✅ Demo complete! Check outputs/ directory for results.")
    print(f"   Task ID: {task_id}")
    print("=" * 60 + "\n")


# ═════════════════════════════════════════════════════════════════════════════
# SLACK MODE (both agents running)
# ═════════════════════════════════════════════════════════════════════════════

def run_hermes_thread() -> None:
    """Run Hermes agent in its own thread."""
    try:
        from agents.hermes import start_hermes
        start_hermes()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"[Hermes] ❌ Fatal error: {exc}")


def run_openclaw_thread() -> None:
    """Run OpenClaw agent in its own thread."""
    try:
        # OpenClaw uses a separate App instance with a different event handler
        # To avoid conflicts with Hermes's App, we import and run it independently
        import importlib, types

        # Dynamically load openclaw to avoid the shared App() conflict
        # In production, run as separate processes instead
        from agents.openclaw import start_openclaw
        start_openclaw()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"[OpenClaw] ❌ Fatal error: {exc}")


def run_both_agents() -> None:
    """
    Start Hermes and OpenClaw in separate threads.

    NOTE: Both agents share the same Slack bot token. In production,
    you would run them as separate processes or use two Slack apps.
    For the hackathon demo, threading works fine since they listen
    to different channels.
    """
    print("🚀 Starting both agents...\n")

    hermes_thread   = threading.Thread(target=run_hermes_thread,   daemon=True, name="Hermes")
    openclaw_thread = threading.Thread(target=run_openclaw_thread, daemon=True, name="OpenClaw")

    hermes_thread.start()
    time.sleep(2)  # Brief stagger so Hermes registers its handlers first
    openclaw_thread.start()

    print("\n✅ Both agents are running!")
    print("   Send a task to #commands in Slack to start the workflow.")
    print("   Press Ctrl+C to stop both agents.\n")

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping agents...")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Forge Sprint 02 — Multi-Agent System Launcher"
    )
    parser.add_argument("--hermes",   action="store_true", help="Start Hermes only")
    parser.add_argument("--openclaw", action="store_true", help="Start OpenClaw only")
    parser.add_argument("--demo",     action="store_true", help="Run local demo (no Slack)")
    args = parser.parse_args()

    print_banner()

    # ── Demo mode ─────────────────────────────────────────────────────────────
    if args.demo:
        run_demo()
        return

    # ── Pre-flight environment check ──────────────────────────────────────────
    missing = check_environment()
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   • {var}")
        print("\n💡 Copy .env.example to .env and fill in your values.")
        sys.exit(1)

    # ── Ollama check ──────────────────────────────────────────────────────────
    if not check_ollama():
        print("⚠️  WARNING: Ollama is not reachable at "
              f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")
        print("   OpenClaw will use fallback demo scripts when Ollama is unavailable.")
        print("   To start Ollama: run 'ollama serve' in a separate terminal.\n")
    else:
        model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder")
        print(f"✅ Ollama is running — model: {model}")

    # ── Start agents ──────────────────────────────────────────────────────────
    if args.hermes:
        from agents.hermes import start_hermes
        start_hermes()
    elif args.openclaw:
        from agents.openclaw import start_openclaw
        start_openclaw()
    else:
        run_both_agents()


if __name__ == "__main__":
    main()
