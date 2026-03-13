from pathlib import Path

def test_readme_contains_mermaid_and_scenarios():
    repo_root = Path(__file__).resolve().parents[1]
    readme_path = repo_root / "README.md"
    
    assert readme_path.exists(), "README.md is missing from repo root"
    
    content = readme_path.read_text()
    
    # Assert Mermaid blocks exist
    assert "```mermaid" in content, "README.md must contain at least one Mermaid diagram block"
    assert "flowchart" in content or "sequenceDiagram" in content, "README.md must contain valid Mermaid syntax"
    
    # Assert Scenarios are mentioned
    expected_scenarios = [
        "default_multihop",
        "delayed_delivery",
        "expiry_before_contact"
    ]
    for scenario in expected_scenarios:
        assert scenario in content, f"README.md must explain the '{scenario}' scenario"
        
    # Assert architecture doc is referenced
    assert "docs/architecture.md" in content, "README.md must link to the architecture documentation"