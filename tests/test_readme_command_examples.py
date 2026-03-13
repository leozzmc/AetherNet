from pathlib import Path

def test_readme_contains_core_commands():
    repo_root = Path(__file__).resolve().parents[1]
    readme_path = repo_root / "README.md"
    
    assert readme_path.exists(), "README.md is missing from repo root"
    
    content = readme_path.read_text()
    
    # Check that users are guided towards the correct tools
    expected_terms = [
        "scripts/run_demo.sh",
        "scripts/run_compare.sh",
        "pytest",
        "make"
    ]
    
    for term in expected_terms:
        assert term in content, f"Expected term '{term}' not found in README.md"