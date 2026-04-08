import pytest

from aether_demo import Phase6DemoArtifactBuilder, Phase6ScenarioRegistry


@pytest.fixture
def artifact_builder() -> Phase6DemoArtifactBuilder:
    return Phase6DemoArtifactBuilder()


def test_build_all_canonical_scenarios(
    artifact_builder: Phase6DemoArtifactBuilder,
) -> None:
    scenario_names = Phase6ScenarioRegistry.get_all_scenario_names()

    for name in scenario_names:
        bundle = artifact_builder.build_from_registry_name(
            scenario_name=name,
            source_node_id="N1",
            destination_node_id="N2",
            time_index=1,
        )

        assert bundle.scenario_name == name
        assert bundle.metadata["source_node_id"] == "N1"
        assert bundle.metadata["candidate_link_count"] > 0

        has_rel = bundle.generated_scenario.reliability_trace is not None
        has_adv = bundle.generated_scenario.adversarial_trace is not None

        if name == Phase6ScenarioRegistry.SCENARIO_CLEAN:
            assert not has_rel and not has_adv
        elif name == Phase6ScenarioRegistry.SCENARIO_DEGRADED:
            assert has_rel and not has_adv
        elif name == Phase6ScenarioRegistry.SCENARIO_JAMMED:
            assert not has_rel and has_adv
        elif name == Phase6ScenarioRegistry.SCENARIO_MIXED:
            assert has_rel and has_adv


def test_invalid_registry_name_raises_value_error(
    artifact_builder: Phase6DemoArtifactBuilder,
) -> None:
    with pytest.raises(ValueError, match="Unknown Phase-6 scenario name"):
        artifact_builder.build_from_registry_name(
            scenario_name="invalid_scenario_name",
            source_node_id="N1",
            destination_node_id="N2",
            time_index=1,
        )


def test_build_from_registry_name_is_deterministic(
    artifact_builder: Phase6DemoArtifactBuilder,
) -> None:
    bundle_a = artifact_builder.build_from_registry_name(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_MIXED,
        source_node_id="N1",
        destination_node_id="N5",
        time_index=5,
    )

    bundle_b = artifact_builder.build_from_registry_name(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_MIXED,
        source_node_id="N1",
        destination_node_id="N5",
        time_index=5,
    )

    assert bundle_a.to_dict() == bundle_b.to_dict()


def test_build_from_spec_is_deterministic(
    artifact_builder: Phase6DemoArtifactBuilder,
) -> None:
    spec = Phase6ScenarioRegistry.get_degraded_network()

    bundle_a = artifact_builder.build_from_spec(
        spec=spec,
        source_node_id="N1",
        destination_node_id="N4",
        time_index=3,
    )
    bundle_b = artifact_builder.build_from_spec(
        spec=spec,
        source_node_id="N1",
        destination_node_id="N4",
        time_index=3,
    )

    assert bundle_a.to_dict() == bundle_b.to_dict()


def test_exported_bundle_is_mutation_safe(
    artifact_builder: Phase6DemoArtifactBuilder,
) -> None:
    bundle = artifact_builder.build_from_registry_name(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_CLEAN,
        source_node_id="N1",
        destination_node_id="N2",
        time_index=1,
    )

    exported = bundle.to_dict()

    exported["metadata"]["builder_name"] = "HACKED"
    exported["routing_context"]["task"]["source_node_id"] = "HACKED"

    exported_again = bundle.to_dict()
    assert exported_again["metadata"]["builder_name"] == "Phase6DemoArtifactBuilder"
    assert exported_again["routing_context"]["task"]["source_node_id"] == "N1"


def test_candidate_link_propagation(
    artifact_builder: Phase6DemoArtifactBuilder,
) -> None:
    bundle = artifact_builder.build_from_registry_name(
        scenario_name=Phase6ScenarioRegistry.SCENARIO_CLEAN,
        source_node_id="N1",
        destination_node_id="N2",
        time_index=1,
        candidate_link_ids=["L1", "L2"],
    )

    assert bundle.metadata["candidate_link_count"] == 2
    assert bundle.routing_context.candidate_link_ids == ["L1", "L2"]

    score_report_links = [score.link_id for score in bundle.routing_score_report.link_scores]
    assert sorted(score_report_links) == ["L1", "L2"]

    decision_links = [
        decision.link_id
        for decision in bundle.security_aware_routing_decision.link_decisions
    ]
    assert sorted(decision_links) == ["L1", "L2"]


def test_input_validation(
    artifact_builder: Phase6DemoArtifactBuilder,
) -> None:
    spec = Phase6ScenarioRegistry.get_clean_baseline()

    with pytest.raises(ValueError, match="source_node_id must be a non-empty string"):
        artifact_builder.build_from_spec(
            spec=spec,
            source_node_id="",
            destination_node_id="N2",
            time_index=1,
        )

    with pytest.raises(ValueError, match="destination_node_id must be a non-empty string"):
        artifact_builder.build_from_spec(
            spec=spec,
            source_node_id="N1",
            destination_node_id="",
            time_index=1,
        )

    with pytest.raises(ValueError, match="time_index cannot be negative"):
        artifact_builder.build_from_spec(
            spec=spec,
            source_node_id="N1",
            destination_node_id="N2",
            time_index=-1,
        )