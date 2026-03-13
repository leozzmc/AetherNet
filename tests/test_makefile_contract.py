from pathlib import Path

def test_makefile_exists_and_has_targets():
    repo_root = Path(__file__).resolve().parents[1]
    makefile_path = repo_root / "Makefile"
    
    assert makefile_path.exists(), "Makefile is missing from repo root"
    
    content = makefile_path.read_text()
    
    # Check for expected targets
    expected_targets = [
        "help:",
        "test:",
        "demo:",
        "compare:",
        "clean-artifacts:"
    ]
    
    for target in expected_targets:
        assert target in content, f"Expected target '{target}' not found in Makefile"