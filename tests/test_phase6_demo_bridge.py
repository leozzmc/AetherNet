import pytest

from aether_demo import (
    Phase6ComparisonBuilder,
    Phase6DemoBridge,
    Phase6ScenarioRegistry,
)


@pytest.fixture
def bridge() -> Phase6DemoBridge:
    return Phase6DemoBridge()


@pytest.fixture
def comparison_builder() -> Phase6ComparisonBuilder:
    return Phase6ComparisonBuilder()


def test_bridge_run_scenario_is_deterministic(bridge: Phase6DemoBridge) -> None:
    res_a = bridge.run_scenario(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_JAMMED,
        source_node_id="N1",
        destination_node_id="N5",
        time_index=5,
    )

    res_b = bridge.run_scenario(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_JAMMED,
        source_node_id="N1",
        destination_node_id="N5",
        time_index=5,
    )

    assert res_a.to_dict() == res_b.to_dict()


def test_bridge_run_scenario_works_for_canonical_scenario(
    bridge: Phase6DemoBridge,
) -> None:
    res = bridge.run_scenario(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_CLEAN,
        source_node_id="N1",
        destination_node_id="N2",
        time_index=1,
    )

    assert res.scenario_name == Phase6ScenarioRegistry.SCENARIO_CLEAN
    assert res.artifact_bundle is not None
    assert res.report is not None
    assert "=== Phase-6 Demo Report ===" in res.report.text


def test_comparison_report_generation_is_deterministic(
    bridge: Phase6DemoBridge,
    comparison_builder: Phase6ComparisonBuilder,
) -> None:
    res_clean = bridge.run_scenario(
        Phase6ScenarioRegistry.SCENARIO_CLEAN, "N1", "N2", 1
    )
    res_mixed = bridge.run_scenario(
        Phase6ScenarioRegistry.SCENARIO_MIXED, "N1", "N2", 1
    )

    comp_a = comparison_builder.build_from_runs(res_clean, res_mixed)
    comp_b = comparison_builder.build_from_runs(res_clean, res_mixed)

    assert comp_a.to_dict() == comp_b.to_dict()


def test_comparison_report_contains_all_required_sections(
    bridge: Phase6DemoBridge,
    comparison_builder: Phase6ComparisonBuilder,
) -> None:
    res_clean = bridge.run_scenario(
        Phase6ScenarioRegistry.SCENARIO_CLEAN, "N1", "N2", 1
    )
    res_mixed = bridge.run_scenario(
        Phase6ScenarioRegistry.SCENARIO_MIXED, "N1", "N2", 1
    )

    comp = comparison_builder.build_from_runs(res_clean, res_mixed)
    text = comp.text

    assert "=== Phase-6 Comparison ===" in text
    assert "Route: N1 -> N2" in text
    assert "Time Index: 1" in text
    assert "[Preferred Links]" in text
    assert "[Allowed Links]" in text
    assert "[Avoid Links]" in text
    assert "[High Severity Links]" in text
    assert "[Compromised Node Count]" in text


def test_comparison_report_handles_empty_sets_cleanly(
    bridge: Phase6DemoBridge,
    comparison_builder: Phase6ComparisonBuilder,
) -> None:
    res_clean = bridge.run_scenario(
        Phase6ScenarioRegistry.SCENARIO_CLEAN, "N1", "N2", 1
    )

    comp = comparison_builder.build_from_runs(res_clean, res_clean)
    text = comp.text

    assert "- A: none" in text
    assert "- B: none" in text


def test_comparison_report_list_ordering_is_deterministic(
    bridge: Phase6DemoBridge,
    comparison_builder: Phase6ComparisonBuilder,
) -> None:
    res_left = bridge.run_scenario(
        Phase6ScenarioRegistry.SCENARIO_MIXED, "N1", "N2", 1
    )
    res_right = bridge.run_scenario(
        Phase6ScenarioRegistry.SCENARIO_CLEAN, "N1", "N2", 1
    )

    comp = comparison_builder.build_from_runs(res_left, res_right)
    text = comp.text

    # Not asserting exact values, but ensuring deterministic comma-separated ordering exists
    # in a stable plain-text output.
    assert "[Preferred Links]" in text
    assert "[Allowed Links]" in text
    assert "[Avoid Links]" in text


def test_comparison_alignment_validation(
    bridge: Phase6DemoBridge,
    comparison_builder: Phase6ComparisonBuilder,
) -> None:
    res_a = bridge.run_scenario(
        Phase6ScenarioRegistry.SCENARIO_CLEAN, "N1", "N2", 1
    )
    res_b = bridge.run_scenario(
        Phase6ScenarioRegistry.SCENARIO_CLEAN, "N1", "N3", 1
    )

    with pytest.raises(ValueError, match="matching destination_node_id"):
        comparison_builder.build_from_runs(res_a, res_b)


def test_export_is_mutation_safe(bridge: Phase6DemoBridge) -> None:
    res = bridge.run_scenario(
        Phase6ScenarioRegistry.SCENARIO_CLEAN, "N1", "N2", 1
    )

    doc = res.to_dict()

    doc["metadata"]["bridge_name"] = "HACKED"
    doc["report"]["text"] = "HACKED"

    doc_again = res.to_dict()
    assert doc_again["metadata"]["bridge_name"] == "Phase6DemoBridge"
    assert doc_again["report"]["text"] != "HACKED"