"""
agents/skills_loader.py
========================
Skills Loader — Parses SKILL.md files and matches keyword triggers.
Used by Hermes to automatically fire the right skill for a given task.

Author : Abishek R
"""

import re
from pathlib import Path

# PyYAML for parsing the YAML frontmatter in SKILL.md files
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class SkillsLoader:
    """
    Scans a skills directory, parses all SKILL.md files, and provides
    keyword-based matching so Hermes can fire the right skill automatically.

    SKILL.md files use YAML frontmatter (between --- delimiters) to define:
        name        : Skill name
        description : What the skill does
        triggers    : List of keyword phrases that activate this skill
    """

    def __init__(self, skills_dir: Path):
        """
        Initialise and load all skills from the directory.

        Args:
            skills_dir : Path to the skills/ directory.
        """
        self.skills_dir = skills_dir
        self.skills: list[dict] = []
        self._load_all()

    def _load_all(self) -> None:
        """
        Walk the skills directory and parse every SKILL.md found.
        """
        if not self.skills_dir.exists():
            return

        for skill_file in self.skills_dir.rglob("SKILL.md"):
            skill = self._parse_skill(skill_file)
            if skill:
                self.skills.append(skill)

        print(f"[SkillsLoader] Loaded {len(self.skills)} skill(s): "
              f"{[s['name'] for s in self.skills]}")

    def _parse_skill(self, path: Path) -> dict | None:
        """
        Parse a single SKILL.md file and extract its metadata.

        Handles both:
          - YAML frontmatter (between --- delimiters)
          - Plain name: / description: / triggers: lines as fallback

        Args:
            path : Absolute path to the SKILL.md file.

        Returns:
            A dict with name, description, triggers, and path.
            Returns None if parsing fails.
        """
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return None

        # Try to extract YAML frontmatter block
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if frontmatter_match and YAML_AVAILABLE:
            try:
                fm = yaml.safe_load(frontmatter_match.group(1))
                if isinstance(fm, dict):
                    return {
                        "name":        fm.get("name", path.parent.name),
                        "description": fm.get("description", ""),
                        "triggers":    fm.get("triggers", []),
                        "path":        str(path),
                    }
            except yaml.YAMLError:
                pass

        # Fallback: simple regex parsing for name/description/triggers
        name = path.parent.name  # Use directory name as fallback
        description = ""
        triggers = []

        name_match = re.search(r"^name:\s*(.+)$", content, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip().strip('"\'')

        desc_match = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
        if desc_match:
            description = desc_match.group(1).strip()

        # Extract triggers list (YAML list format: "  - keyword")
        trigger_matches = re.findall(r"^\s+-\s+(.+)$", content, re.MULTILINE)
        if trigger_matches:
            triggers = [t.strip() for t in trigger_matches]

        return {
            "name":        name,
            "description": description,
            "triggers":    triggers,
            "path":        str(path),
        }

    def match(self, text: str) -> dict | None:
        """
        Check if any loaded skill's trigger keywords match the given text.

        Case-insensitive substring matching — any trigger phrase found
        anywhere in the text activates the skill.

        Args:
            text : The user's task message to match against.

        Returns:
            The first matching skill dict, or None if no match.
        """
        text_lower = text.lower()
        for skill in self.skills:
            for trigger in skill.get("triggers", []):
                if trigger.lower() in text_lower:
                    return skill
        return None

    def list_skills(self) -> list[dict]:
        """Return all loaded skills (name, description, trigger count)."""
        return [
            {
                "name":          s["name"],
                "description":   s["description"],
                "trigger_count": len(s.get("triggers", [])),
            }
            for s in self.skills
        ]
