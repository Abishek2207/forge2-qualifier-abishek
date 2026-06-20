"""
run_system.py — FIXED STABLE VERSION (Forge 2)
=============================================
Hermes + OpenClaw safe launcher
"""

import argparse
import os
import sys
import time
import subprocess
from dotenv import load_dotenv

load_dotenv()


# ─────────────────────────────────────────────
# ENV CHECK
# ─────────────────────────────────────────────
def check_env():
    required = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "GROQ_API_KEY"]
    return [v for v in required if not os.getenv(v)]


# ─────────────────────────────────────────────
# BANNER
# ─────────────────────────────────────────────
def banner():
    print("""
╔══════════════════════════════════════════════╗
║   FORGE 2 MULTI-AGENT SYSTEM (STABLE FIX)   ║
║   Hermes + OpenClaw                         ║
╚══════════════════════════════════════════════╝
""")


# ─────────────────────────────────────────────
# START PROCESS (SAFE WRAPPER)
# ─────────────────────────────────────────────
def start_process(module_name: str):
    """
    Starts a python module safely and ensures:
    ✔ No silent crash
    ✔ Proper process group
    """

    return subprocess.Popen(
        [sys.executable, "-m", module_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        if os.name == "nt" else 0
    )


# ─────────────────────────────────────────────
# RUN AGENTS
# ─────────────────────────────────────────────
def run_agents():

    print("🚀 Starting Hermes + OpenClaw...\n")

    hermes = start_process("agents.hermes")
    openclaw = start_process("agents.openclaw")

    print("✅ Hermes started")
    print("✅ OpenClaw started")
    print("📡 System LIVE — waiting for Slack commands...\n")

    try:
        while True:

            # ── WATCHDOG (IMPORTANT) ──
            if hermes.poll() is not None:
                print("❌ Hermes stopped unexpectedly")
                print(hermes.stdout.read() if hermes.stdout else "")
                break

            if openclaw.poll() is not None:
                print("❌ OpenClaw stopped unexpectedly")
                print(openclaw.stdout.read() if openclaw.stdout else "")
                break

            # lightweight heartbeat
            print("💓 system alive...")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n🛑 Stopping agents...")

        hermes.terminate()
        openclaw.terminate()

        hermes.wait()
        openclaw.wait()

        print("✅ Clean shutdown complete")


# ─────────────────────────────────────────────
# DEMO MODE
# ─────────────────────────────────────────────
def run_demo():
    print("🎬 Demo Mode")
    print("✔ Hermes planning simulated")
    print("✔ OpenClaw execution simulated")
    print("✔ Output generated")
    print("✅ Done")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--hermes", action="store_true")
    parser.add_argument("--openclaw", action="store_true")
    args = parser.parse_args()

    banner()

    missing = check_env()
    if missing:
        print("❌ Missing ENV variables:")
        for m in missing:
            print(" -", m)
        sys.exit(1)

    if args.demo:
        run_demo()
        return

    if args.hermes:
        subprocess.call([sys.executable, "-m", "agents.hermes"])
        return

    if args.openclaw:
        subprocess.call([sys.executable, "-m", "agents.openclaw"])
        return

    run_agents()


if __name__ == "__main__":
    main()