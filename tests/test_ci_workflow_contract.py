from pathlib import Path

def test_github_actions_workflow_is_ready():
    repo_root = Path(__file__).resolve().parents[1]
    workflow_path = repo_root / ".github" / "workflows" / "test.yml"
    
    assert workflow_path.exists(), "GitHub Actions workflow test.yml is missing"
    
    content = workflow_path.read_text()
    
    # Check for crucial CI steps
    assert "actions/setup-python" in content, "CI must setup Python"
    assert "requirements-dev.txt" in content, "CI must install developer dependencies"
    assert "make ci-test" in content or "pytest" in content, "CI must run tests"