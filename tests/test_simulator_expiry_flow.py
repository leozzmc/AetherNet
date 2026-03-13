import json
import tempfile
from pathlib import Path

from sim.simulator import create_default_simulator
from router.bundle import Bundle


def test_simulator_does_not_forward_expired_bundles():
    plan = {
        "simulation_duration_sec": 30,
        "contacts": [
            {
                "source": "lunar-node",
                "target": "leo-relay",
                "start_time": 20,
                "end_time": 25,
                "one_way_delay_ms": 100,
                "bandwidth_kbit": 100,
                "bidirectional": False,
            }
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(plan, plan_file)
        plan_path = Path(plan_file.name)

    try:
        with tempfile.TemporaryDirectory() as tmpstore:
            sim, _ = create_default_simulator(str(plan_path), tmpstore, tick_size=1)

            b_short = Bundle(
                id="short-1",
                type="telemetry",
                source="lunar-node",
                destination="ground-station",
                priority=100,
                created_at=0,
                ttl_sec=10,
                size_bytes=10,
                payload_ref="payloads/telemetry/short-1.json",
            )
            sim.lunar_queue.enqueue(b_short)
            sim.store.save_bundle(b_short)

            metrics = sim.run()

            assert "short-1" in metrics["recent_purged_ids"]
            assert sim.store.exists("short-1") is False
            assert "telemetry" in metrics["bundles_expired_total"]
            assert metrics["bundles_expired_total"]["telemetry"] >= 1
    finally:
        if plan_path.exists():
            plan_path.unlink()