from pathlib import Path

def test_gitignore_contains_key_patterns():
    repo_root = Path(__file__).resolve().parents[1]
    gitignore_path = repo_root / ".gitignore"
    
    assert gitignore_path.exists(), ".gitignore is missing from repo root"
    
    content = gitignore_path.read_text()
    
    expected_patterns = [
        "__pycache__/",
        ".venv/",
        ".pytest_cache/",
        "artifacts/"
    ]
    
    for pattern in expected_patterns:
        assert pattern in content, f"Expected pattern '{pattern}' not found in .gitignore"