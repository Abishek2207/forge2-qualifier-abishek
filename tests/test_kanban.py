import os

def test_frontend_files_exist():
    assert os.path.exists("frontend/src/App.jsx")
    assert os.path.exists("frontend/src/index.css")
    assert os.path.exists("frontend/package.json")

def test_evidence_files_exist():
    assert os.path.exists("EVIDENCE.md")
    assert os.path.exists("ARCHITECTURE.md")
    assert os.path.exists("QUALIFIER_CHECKLIST.md")
    assert os.path.exists("screenshots/README.md")
    assert os.path.exists("agent-log.md")
