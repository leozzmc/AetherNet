import json
import tempfile
from pathlib import Path
from sim.run_helpers import run_named_scenario

def test_timeline_is_recorded_and_serializable():
    with tempfile.TemporaryDirectory() as tmpdir:
        report = run_named_scenario("default_multihop", output_path=None)
        
        assert "bundle_timelines" in report
        timelines = report["bundle_timelines"]
        
        # Verify telemetry bundle timeline shape
        assert "tel-001" in timelines
        t_tel = timelines["tel-001"]
        assert "first_forwarded_tick" in t_tel
        assert "stored_tick" in t_tel
        assert "delivered_tick" in t_tel
        
        # Must be JSON serializable
        json.dumps(timelines)