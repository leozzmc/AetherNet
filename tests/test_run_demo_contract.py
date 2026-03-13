import json
import tempfile
from pathlib import Path

from sim.simulator import create_default_simulator


def test_simulator_factory_and_snapshot_contract():
    plan = {
        "simulation_duration_sec": 1,
        "contacts": [],
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(plan, plan_file)
        plan_path = Path(plan_file.name)

    try:
        with tempfile.TemporaryDirectory() as tmpstore:
            sim, _ = create_default_simulator(str(plan_path), tmpstore)
            snapshot = sim.run()

            assert "bundles_forwarded_total" in snapshot
            assert "bundles_delivered_total" in snapshot
            assert "bundles_stored_total" in snapshot
            assert "bundles_expired_total" in snapshot
            assert "last_queue_depths" in snapshot
            assert "recent_purged_ids" in snapshot

            json.dumps(snapshot)
    finally:
        if plan_path.exists():
            plan_path.unlink()