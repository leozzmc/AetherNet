import tempfile
import json
from pathlib import Path

from sim.scenarios import list_scenarios, get_scenario
from sim.simulator import create_default_simulator
from sim.reporting import compare_reports


def test_all_scenarios_can_be_compared():
    all_reports = []

    for scenario_name in list_scenarios():
        profile = get_scenario(scenario_name)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as plan_file:
            json.dump(profile.generate_plan(), plan_file)
            plan_path = plan_file.name

        try:
            with tempfile.TemporaryDirectory() as tmpstore:
                sim, _ = create_default_simulator(
                    plan_path=plan_path,
                    store_dir=tmpstore,
                    scenario_name=profile.name,
                    inject_short_lived=profile.inject_short_lived_bundle,
                )
                report = sim.run()
                all_reports.append(report)
        finally:
            Path(plan_path).unlink()

    comparison = compare_reports(all_reports)

    assert len(comparison["scenario_names"]) == len(list_scenarios())
    assert len(comparison["per_scenario_summaries"]) == len(list_scenarios())
    assert "aggregate" in comparison
    assert "total_delivered_bundles" in comparison["aggregate"]

    json.dumps(comparison)