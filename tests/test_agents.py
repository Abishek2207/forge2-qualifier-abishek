import pytest
from pathlib import Path
import json

def test_memory_file_creation():
    """Test that Hermes memory file exists and is valid JSON."""
    memory_path = Path("memory/hermes_memory.json")
    assert memory_path.exists(), "Memory file should exist."
    
    with open(memory_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "facts" in data
    assert "task_history" in data
    assert data["agent"] == "Hermes"

def test_skills_loader_dummy():
    """Test that skills loader module is importable."""
    from agents.skills_loader import SkillsLoader
    assert SkillsLoader is not None

def test_env_example_exists():
    """Ensure the .env.example file is present."""
    assert Path(".env.example").exists()

def test_requirements_exists():
    """Ensure requirements.txt is present."""
    assert Path("requirements.txt").exists()
