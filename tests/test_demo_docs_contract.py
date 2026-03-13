from pathlib import Path

def test_demo_docs_exist():
    root = Path(__file__).resolve().parents[1]

    assert (root / "docs/demo.md").exists()
    assert (root / "docs/artifacts.md").exists()