from pathlib import Path

def test_smoke_contract_in_makefile():
    repo_root = Path(__file__).resolve().parents[1]
    makefile_path = repo_root / "Makefile"
    
    assert makefile_path.exists(), "Makefile is missing"
    
    content = makefile_path.read_text()
    assert "smoke:" in content, "Makefile must have a 'smoke' target"
    assert "demo" in content and "test-fast" in content, "Smoke target should combine demo and fast tests"

def test_smoke_mentioned_in_docs():
    repo_root = Path(__file__).resolve().parents[1]
    dev_docs = repo_root / "docs" / "development.md"
    readme = repo_root / "README.md"
    
    assert dev_docs.exists() and readme.exists()
    
    assert "make smoke" in dev_docs.read_text(), "make smoke must be documented in development.md"
    assert "make smoke" in readme.read_text(), "make smoke must be mentioned in README quickstart"