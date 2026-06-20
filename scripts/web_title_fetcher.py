"""
web_title_fetcher.py
====================
OpenClaw Coding Agent — Forge 2 Qualifier Script

Purpose:
    Fetch the HTML <title> tag from 3 URLs, capture the HTTP status code
    for each, save structured results to outputs/results.json, and print
    a formatted summary report to the terminal.

Usage:
    python scripts/web_title_fetcher.py

Output:
    - outputs/results.json   (JSON array with url, status_code, title)
    - Printed report to stdout

Author : Abishek R (via OpenClaw coding agent)
Model  : Qwen2.5-Coder via Ollama
Date   : June 2026
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ── Third-party dependency (install with: pip install requests) ──────────────
try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not found.")
    print("Run: pip install requests")
    sys.exit(1)


# ── Configuration ─────────────────────────────────────────────────────────────

# The 3 URLs to fetch. All are publicly accessible with no authentication.
URLS_TO_FETCH = [
    "https://www.python.org",           # Python official site
    "https://github.com",               # GitHub (our version control)
    "https://groq.com",                 # Groq — provides Kimi K2 API for Hermes
]

# Where to save the JSON output (relative to project root)
OUTPUT_DIR  = "outputs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "results.json")

# Network timeout in seconds — prevents the script from hanging on slow servers
REQUEST_TIMEOUT = 10


# ── Helper Functions ──────────────────────────────────────────────────────────

def extract_title(html: str) -> str:
    """
    Extract the text content of the first <title> tag found in an HTML string.

    Args:
        html: Raw HTML string from the HTTP response body.

    Returns:
        The page title as a stripped string, or "No title found" if missing.
    """
    # Use regex to find <title>...</title> — works without parsing the full DOM
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if match:
        # Strip whitespace and normalise internal newlines
        return " ".join(match.group(1).split())
    return "No title found"


def fetch_url(url: str) -> dict:
    """
    Perform an HTTP GET request for the given URL and return a result dict.

    Args:
        url: The URL to fetch.

    Returns:
        A dict with keys: url, status_code, title, error (if any).

    This function never raises — on any network or HTTP error it returns
    a result with status_code=null and title="ERROR: <message>".
    This way a single broken URL does not crash the whole run.
    """
    print(f"  Fetching: {url}")
    try:
        # Send GET request with a timeout to avoid hanging forever
        response = requests.get(url, timeout=REQUEST_TIMEOUT, headers={
            # Some servers reject requests without a User-Agent header
            "User-Agent": "OpenClaw-Fetcher/1.0 (Forge2Qualifier)"
        })
        title = extract_title(response.text)

        return {
            "url":         url,
            "status_code": response.status_code,
            "title":       title,
            "error":       None,
        }

    except requests.exceptions.Timeout:
        # Server did not respond within REQUEST_TIMEOUT seconds
        return {
            "url":         url,
            "status_code": None,
            "title":       "ERROR: Request timed out",
            "error":       "Timeout",
        }

    except requests.exceptions.ConnectionError as exc:
        # DNS failure, refused connection, etc.
        return {
            "url":         url,
            "status_code": None,
            "title":       f"ERROR: Connection failed — {exc}",
            "error":       "ConnectionError",
        }

    except requests.exceptions.RequestException as exc:
        # Catch-all for any other requests-related error
        return {
            "url":         url,
            "status_code": None,
            "title":       f"ERROR: {exc}",
            "error":       "RequestException",
        }


def save_results(results: list, run_timestamp: str) -> None:
    """
    Save the list of fetch results to outputs/results.json.

    The JSON file includes a metadata block (run time, agent info) and
    the array of individual URL results.

    Args:
        results: List of result dicts from fetch_url().
        run_timestamp: ISO 8601 timestamp of this run.
    """
    # Create the outputs/ directory if it does not already exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Build the full payload — wrap results in metadata so the file is self-describing
    payload = {
        "meta": {
            "run_at":   run_timestamp,
            "agent":    "OpenClaw",
            "model":    "Qwen2.5-Coder via Ollama",
            "script":   "scripts/web_title_fetcher.py",
            "forge":    "Forge 2 Edition 1 Qualifier",
            "author":   "Abishek R",
            "url_count": len(results),
        },
        "results": results,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        # indent=2 makes the file human-readable for demo purposes
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n  ✅ Saved to: {OUTPUT_FILE}")


def print_report(results: list, run_timestamp: str) -> None:
    """
    Print a formatted, human-readable summary to the terminal.

    This is the 'structured report' shown during demos to prove the
    script ran successfully and produced real data.

    Args:
        results: List of result dicts from fetch_url().
        run_timestamp: ISO 8601 timestamp of this run.
    """
    width = 64
    print("\n" + "═" * width)
    print("  WEB TITLE FETCHER — RESULTS REPORT")
    print(f"  OpenClaw Coding Agent | Forge 2 Qualifier")
    print(f"  Run Time : {run_timestamp}")
    print("═" * width)

    for i, result in enumerate(results, start=1):
        status = result["status_code"]
        title  = result["title"]
        url    = result["url"]

        # Show ✅ for HTTP 2xx responses, ❌ for errors / non-2xx
        if status and 200 <= status < 300:
            indicator = "✅"
        else:
            indicator = "❌"

        print(f"\n  [{i}] {indicator}  {url}")
        print(f"       Status : {status if status else 'N/A'}")
        print(f"       Title  : {title}")

    # Summary line
    successes = sum(1 for r in results if r["status_code"] and 200 <= r["status_code"] < 300)
    failures  = len(results) - successes

    print("\n" + "─" * width)
    print(f"  Total URLs : {len(results)}")
    print(f"  Success    : {successes}")
    print(f"  Failed     : {failures}")
    print(f"  Output     : {OUTPUT_FILE}")
    print("═" * width + "\n")


# ── Main Entry Point ──────────────────────────────────────────────────────────

def main():
    """
    Main function — orchestrates the full fetch-save-report pipeline.

    Steps:
        1. Record the run timestamp
        2. Fetch all URLs in URLS_TO_FETCH
        3. Save results to outputs/results.json
        4. Print the structured report
    """
    # Record the exact time this run started (UTC, ISO 8601 format)
    run_timestamp = datetime.now(timezone.utc).isoformat()

    print("\n🦾 OpenClaw Web Title Fetcher — Starting")
    print(f"   Fetching {len(URLS_TO_FETCH)} URL(s)...\n")

    # Step 1: Fetch all URLs
    results = [fetch_url(url) for url in URLS_TO_FETCH]

    # Step 2: Save structured JSON output
    save_results(results, run_timestamp)

    # Step 3: Print the human-readable report
    print_report(results, run_timestamp)


# Run main() only when this script is executed directly (not imported)
if __name__ == "__main__":
    main()
