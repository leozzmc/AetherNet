import tempfile
from pathlib import Path
from sim.run_helpers import run_named_scenario

def test_run_named_scenario_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "test_report.json"
        
        # Helper should abstract all temporary plan files and return a valid report dict
        report = run_named_scenario("default_multihop", output_path=out_path)
        
        assert "scenario_name" in report
        assert report["scenario_name"] == "default_multihop"
        
        # Verify the helper correctly wrote the file
        assert out_path.exists()