from pathlib import Path

def test_architecture_doc_contains_key_concepts():
    repo_root = Path(__file__).resolve().parents[1]
    arch_path = repo_root / "docs" / "architecture.md"
    
    assert arch_path.exists(), "docs/architecture.md is missing"
    
    content = arch_path.read_text()
    
    # Assert Mermaid exists
    assert "```mermaid" in content, "architecture.md must contain a Mermaid diagram block"
    
    # Assert key modules are explained
    expected_modules = ["sim/", "router/", "bundle_queue/", "store/"]
    for module in expected_modules:
        assert module in content, f"architecture.md must explain the responsibility of '{module}'"
        
    # Assert topology is mentioned
    assert "lunar-node" in content and "ground-station" in content, "architecture.md must mention the reference topology"