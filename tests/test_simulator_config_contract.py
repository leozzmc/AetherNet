import tempfile
import json
from pathlib import Path

from sim.simulator import create_default_simulator
from sim.scenarios import get_scenario


def test_simulator_config_overrides():
    profile = get_scenario("default_multihop")

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
        json.dump(profile.generate_plan(), plan_file)
        plan_path = Path(plan_file.name)

    try:
        with tempfile.TemporaryDirectory() as tmpstore_a:
            sim, _ = create_default_simulator(
                plan_path=str(plan_path),
                store_dir=tmpstore_a,
                scenario_name=profile.name,
                tick_size=2,
                simulation_end_override=5,
            )

            assert sim.scenario_name == "default_multihop"
            assert sim.clock.tick_size == 2
            assert sim.clock.end_time == 5

        with tempfile.TemporaryDirectory() as tmpstore_b:
            _, bundles = create_default_simulator(
                plan_path=str(plan_path),
                store_dir=tmpstore_b,
                inject_short_lived=True,
            )

            assert any(b.id == "tel-short" for b in bundles)
    finally:
        if plan_path.exists():
            plan_path.unlink()