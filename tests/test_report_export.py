import tempfile
import json
from pathlib import Path

from sim.simulator import create_default_simulator


def test_report_structure_and_serialization():
    plan = {"simulation_duration_sec": 1, "contacts": []}
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(plan, plan_file)
        plan_path = Path(plan_file.name)

    try:
        with tempfile.TemporaryDirectory() as tmpstore:
            sim, _ = create_default_simulator(str(plan_path), tmpstore)
            report = sim.run()

            assert "scenario_name" in report
            assert "simulation_start_time" in report
            assert "simulation_end_time" in report
            assert "tick_size" in report
            assert "final_metrics" in report
            assert "store_bundle_ids_remaining" in report
            assert "delivered_bundle_ids" in report
            assert "purged_bundle_ids" in report

            json_str = json.dumps(report)
            assert "scenario_name" in json_str
    finally:
        if plan_path.exists():
            plan_path.unlink()