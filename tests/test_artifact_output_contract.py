import tempfile
import json
from pathlib import Path
from sim.reporting import write_json_report

def test_json_report_writing_and_path_creation():
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir) / "artifacts"
        report_path = base_dir / "reports" / "test_scenario.json"
        
        mock_data = {"test": "data"}
        
        # Ensure directories are created and file is written
        written_path = write_json_report(mock_data, report_path)
        
        assert written_path.exists()
        assert written_path.parent.name == "reports"
        assert written_path.parent.parent.name == "artifacts"
        
        with written_path.open() as f:
            loaded = json.load(f)
            assert loaded["test"] == "data"