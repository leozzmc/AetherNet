from pathlib import Path

def test_requirements_dev_exists_and_contains_pytest():
    repo_root = Path(__file__).resolve().parents[1]
    req_path = repo_root / "requirements-dev.txt"
    
    assert req_path.exists(), "requirements-dev.txt is missing from repo root"
    
    content = req_path.read_text().lower()
    
    assert "pytest" in content, "requirements-dev.txt must include pytest"
    
    # Ensure it's reasonably concise (preventing bloat)
    lines = [line for line in content.splitlines() if line.strip() and not line.startswith("#")]
    assert len(lines) < 10, "requirements-dev.txt seems bloated for MVP scope"