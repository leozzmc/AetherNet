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


def test_simulator_factory_accepts_routing_mode_override():
    plan = {
        "simulation_duration_sec": 30,
        "contacts": [
            {
                "source": "lunar-node",
                "target": "leo-relay",
                "start_time": 0,
                "end_time": 10,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 128,
                "bidirectional": False,
            },
            {
                "source": "leo-relay",
                "target": "ground-station",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 10,
                "bandwidth_kbit": 128,
                "bidirectional": False,
            },
        ],
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(plan, plan_file)
        plan_path = Path(plan_file.name)

    try:
        with tempfile.TemporaryDirectory() as tmpstore:
            sim, _ = create_default_simulator(
                str(plan_path),
                tmpstore,
                routing_mode="contact_aware",
            )
            snapshot = sim.run()

            assert snapshot["routing_mode"] == "contact_aware"
    finally:
        if plan_path.exists():
            plan_path.unlink()


def test_multipath_friendly_scenario_highlights_mode_difference():
    from sim.scenarios import get_scenario

    profile = get_scenario("multipath_competition")
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(profile.generate_plan(), plan_file)
        plan_path = Path(plan_file.name)

    try:
        with tempfile.TemporaryDirectory() as tmpstore_baseline:
            sim, _ = create_default_simulator(
                str(plan_path),
                tmpstore_baseline,
                scenario_name=profile.name,
                routing_mode="baseline",
            )
            baseline = sim.run()

        with tempfile.TemporaryDirectory() as tmpstore_multipath:
            sim, _ = create_default_simulator(
                str(plan_path),
                tmpstore_multipath,
                scenario_name=profile.name,
                routing_mode="multipath",
            )
            multipath = sim.run()

        assert baseline["final_metrics"]["delivery_ratio"] == 0.0
        assert multipath["final_metrics"]["delivery_ratio"] == 1.0
    finally:
        if plan_path.exists():
            plan_path.unlink()


def test_contact_timing_tradeoff_highlights_contact_aware_difference():
    from sim.scenarios import get_scenario

    profile = get_scenario("contact_timing_tradeoff")
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(profile.generate_plan(), plan_file)
        plan_path = Path(plan_file.name)

    try:
        with tempfile.TemporaryDirectory() as tmpstore_baseline:
            sim, _ = create_default_simulator(
                str(plan_path),
                tmpstore_baseline,
                scenario_name=profile.name,
                routing_mode="baseline",
            )
            baseline = sim.run()

        with tempfile.TemporaryDirectory() as tmpstore_contact:
            sim, _ = create_default_simulator(
                str(plan_path),
                tmpstore_contact,
                scenario_name=profile.name,
                routing_mode="contact_aware",
            )
            contact_aware = sim.run()

        assert baseline["final_metrics"]["delivery_ratio"] == 0.0
        assert contact_aware["final_metrics"]["delivery_ratio"] == 1.0
    finally:
        if plan_path.exists():
            plan_path.unlink()
