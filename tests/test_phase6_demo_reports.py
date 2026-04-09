import pytest

from aether_demo import (
    Phase6DemoArtifactBuilder,
    Phase6DemoReportBuilder,
    Phase6ScenarioRegistry,
)


@pytest.fixture
def artifact_builder() -> Phase6DemoArtifactBuilder:
    return Phase6DemoArtifactBuilder()


@pytest.fixture
def report_builder() -> Phase6DemoReportBuilder:
    return Phase6DemoReportBuilder()


def test_report_generation_is_deterministic(
    artifact_builder: Phase6DemoArtifactBuilder,
    report_builder: Phase6DemoReportBuilder,
) -> None:
    """Verify identical bundles produce identical text reports."""
    bundle_a = artifact_builder.build_from_registry_name(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_MIXED,
        source_node_id="N1",
        destination_node_id="N2",
        time_index=1,
    )
    bundle_b = artifact_builder.build_from_registry_name(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_MIXED,
        source_node_id="N1",
        destination_node_id="N2",
        time_index=1,
    )

    report_a = report_builder.build(bundle_a)
    report_b = report_builder.build(bundle_b)

    assert report_a.text == report_b.text
    assert report_a.to_dict() == report_b.to_dict()


def test_report_contains_all_sections(
    artifact_builder: Phase6DemoArtifactBuilder,
    report_builder: Phase6DemoReportBuilder,
) -> None:
    """Verify the structural integrity of the report format."""
    bundle = artifact_builder.build_from_registry_name(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_CLEAN,
        source_node_id="N1",
        destination_node_id="N2",
        time_index=1,
    )
    report = report_builder.build(bundle)
    text = report.text

    assert "=== Phase-6 Demo Report ===" in text
    assert "[Scenario Summary]" in text
    assert "[Observed Conditions]" in text
    assert "[Probabilistic Scores]" in text
    assert "[Security Signals]" in text
    assert "[Security-Aware Decision]" in text


def test_clean_scenario_empty_conditions(
    artifact_builder: Phase6DemoArtifactBuilder,
    report_builder: Phase6DemoReportBuilder,
) -> None:
    """Verify that a clean scenario cleanly renders 'none' for hostile states."""
    bundle = artifact_builder.build_from_registry_name(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_CLEAN,
        source_node_id="N1",
        destination_node_id="N2",
        time_index=1,
    )
    report = report_builder.build(bundle)
    text = report.text

    assert "Degraded Links: none" in text
    assert "Jammed Links: none" in text
    assert "Malicious Drop Links: none" in text
    assert "Compromised Nodes: none" in text


def test_mixed_scenario_renders_conditions_and_decisions(
    artifact_builder: Phase6DemoArtifactBuilder,
    report_builder: Phase6DemoReportBuilder,
) -> None:
    """Verify that active traces are properly parsed and mapped to the report."""
    bundle = artifact_builder.build_from_registry_name(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_MIXED,
        source_node_id="N1",
        destination_node_id="N5",
        time_index=5,
    )
    report = report_builder.build(bundle)
    text = report.text

    # Basic presence checks for mixed threats
    assert "Reliability Trace: enabled" in text
    assert "Adversarial Trace: enabled" in text
    
    # Ensure decision categories exist
    assert "Preferred: " in text
    assert "Allowed: " in text
    assert "Avoid: " in text
    
    # We should see some scores with reasons populated
    assert "reasons=" in text


def test_stable_line_ordering(
    artifact_builder: Phase6DemoArtifactBuilder,
    report_builder: Phase6DemoReportBuilder,
) -> None:
    """Verify that list outputs in the report maintain deterministic alphabetical sorting."""
    bundle = artifact_builder.build_from_registry_name(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_CLEAN,
        source_node_id="N1",
        destination_node_id="N2",
        time_index=1,
        candidate_link_ids=["L3", "L1", "L2"], # Pass unsorted
    )
    report = report_builder.build(bundle)
    text = report.text
    
    # Check Probabilistic Scores block order
    lines = text.split("\n")
    scores_idx = lines.index("[Probabilistic Scores]")
    
    assert lines[scores_idx + 1].startswith("L1 ->")
    assert lines[scores_idx + 2].startswith("L2 ->")
    assert lines[scores_idx + 3].startswith("L3 ->")


def test_export_mutation_safety(
    artifact_builder: Phase6DemoArtifactBuilder,
    report_builder: Phase6DemoReportBuilder,
) -> None:
    """Verify that mutating the dictionary export does not leak back to the object."""
    bundle = artifact_builder.build_from_registry_name(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_CLEAN,
        source_node_id="N1",
        destination_node_id="N2",
        time_index=1,
    )
    report = report_builder.build(bundle)
    
    doc = report.to_dict()
    
    # Mutate
    doc["metadata"]["builder_name"] = "HACKED"
    doc["text"] = "HACKED TEXT"
    
    # Verify original is safe
    doc_again = report.to_dict()
    assert doc_again["metadata"]["builder_name"] == "Phase6DemoReportBuilder"
    assert doc_again["text"] != "HACKED TEXT"