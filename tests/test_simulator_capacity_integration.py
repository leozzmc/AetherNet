import json
import tempfile
from pathlib import Path

from sim.simulator import create_default_simulator


def test_simulator_respects_capacity_limits():
    plan = {
        "simulation_duration_sec": 30,
        "contacts": [
            {
                "source": "lunar-node",
                "target": "leo-relay",
                "start_time": 0,
                "end_time": 20,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 1000,
                "capacity_bundles": 2,
            },
            {
                "source": "leo-relay",
                "target": "ground-station",
                "start_time": 0,
                "end_time": 20,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 1000,
            },
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(plan, plan_file)
        plan_path = plan_file.name

    try:
        with tempfile.TemporaryDirectory() as tmpstore:
            sim, _ = create_default_simulator(
                plan_path=plan_path,
                store_dir=tmpstore,
                scenario_name="capacity_test",
            )
            report = sim.run()

            delivered_ids = set(report.get("delivered_bundle_ids", []))
            remaining_ids = set(report.get("store_bundle_ids_remaining", []))

            assert delivered_ids == {"tel-001", "tel-002"}
            assert "sci-001" in remaining_ids

            final_metrics = report.get("final_metrics", {})
            forwarded = final_metrics.get("bundles_forwarded_total", {})
            delivered = final_metrics.get("bundles_delivered_total", {})

            assert forwarded.get("telemetry", 0) == 4
            assert delivered.get("telemetry", 0) == 2
            assert delivered.get("science", 0) == 0

    finally:
        Path(plan_path).unlink()