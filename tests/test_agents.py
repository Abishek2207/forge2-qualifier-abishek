import pytest
from pathlib import Path
import json

def test_required_files_exist():
    """Verify that all required files and folders for the qualifier exist."""
    assert Path("README.md").exists()
    assert Path("agent-log.md").exists()
    assert Path("memory/hermes_memory.json").exists()
    assert Path("outputs/").exists()
    assert Path("skills/hello-world/SKILL.md").exists()
    assert Path("skills/forge-status/SKILL.md").exists()

def test_memory_file_valid():
    """Verify that the memory file is valid JSON and contains required fields."""
    memory_path = Path("memory/hermes_memory.json")
    with open(memory_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "facts" in data
    assert data["facts"]["builder_name"] == "Abishek R"
    assert "skill_triggers_fired" in data

def test_agent_log_format():
    """Verify that agent-log.md contains the exact required phrases."""
    log_content = Path("agent-log.md").read_text(encoding="utf-8")
    assert "What I Did" in log_content
    assert "What's Left" in log_content
    assert "What Needs Your Call" in log_content

def test_results_json_valid():
    """Verify that outputs/results.json is valid JSON if it exists."""
    results_path = Path("outputs/results.json")
    if results_path.exists():
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "task" in data
        assert "status" in data
