import pytest

from aether_adversarial import (
    AdversarialTrace,
    DelayInjectionEvent,
    JammingEvent,
    MaliciousDropEvent,
    NodeCompromiseEvent,
)
from aether_reliability import (
    DegradationEvent,
    DelayEvent,
    LinkReliabilityTrace,
)
from aether_routing_context import ObservationBuilder, RoutingContextBuilder
from aether_scenarios import GeneratedScenario


def create_mock_scenario(
    rel_trace=None,
    adv_trace=None,
    time_horizon=5,
) -> GeneratedScenario:
    return GeneratedScenario(
        scenario_name="test_scene",
        master_seed=42,
        node_ids=["N1", "N2", "N3"],
        link_ids=["L1", "L2", "L3"],
        time_indices=list(range(time_horizon)),
        metadata={"mock": True},
        reliability_trace=rel_trace,
        adversarial_trace=adv_trace,
    )


def test_observation_without_traces() -> None:
    scenario = create_mock_scenario()
    observation = ObservationBuilder().build(scenario, 2)

    assert observation.time_index == 2
    assert observation.degraded_links == []
    assert observation.extra_delay_ms_by_link == {}
    assert observation.jammed_links == []
    assert observation.malicious_drop_links == []
    assert observation.compromised_nodes == []
    assert observation.injected_delay_ms_by_link == {}


def test_observation_with_reliability_trace() -> None:
    reliability_trace = LinkReliabilityTrace()
    reliability_trace.add_degradation_event(
        DegradationEvent("L1", 2, degraded=True)
    )
    reliability_trace.add_delay_event(
        DelayEvent("L2", 2, extra_delay_ms=50)
    )
    reliability_trace.add_delay_event(
        DelayEvent("L2", 3, extra_delay_ms=999)
    )

    scenario = create_mock_scenario(rel_trace=reliability_trace)
    observation = ObservationBuilder().build(scenario, 2)

    assert observation.degraded_links == ["L1"]
    assert observation.extra_delay_ms_by_link == {"L2": 50}
    assert observation.jammed_links == []
    assert observation.malicious_drop_links == []
    assert observation.compromised_nodes == []
    assert observation.injected_delay_ms_by_link == {}


def test_observation_with_adversarial_trace() -> None:
    adversarial_trace = AdversarialTrace()
    adversarial_trace.add_jamming_event(JammingEvent("L1", 2, jammed=True))
    adversarial_trace.add_malicious_drop_event(
        MaliciousDropEvent("L2", 2, drop=True)
    )
    adversarial_trace.add_delay_injection_event(
        DelayInjectionEvent("L3", 2, injected_delay_ms=25)
    )
    adversarial_trace.add_node_compromise_event(
        NodeCompromiseEvent("N3", 2, compromised=True)
    )

    scenario = create_mock_scenario(adv_trace=adversarial_trace)
    observation = ObservationBuilder().build(scenario, 2)

    assert observation.jammed_links == ["L1"]
    assert observation.malicious_drop_links == ["L2"]
    assert observation.injected_delay_ms_by_link == {"L3": 25}
    assert observation.compromised_nodes == ["N3"]
    assert observation.degraded_links == []
    assert observation.extra_delay_ms_by_link == {}


def test_time_index_validation() -> None:
    scenario = create_mock_scenario(time_horizon=3)
    builder = ObservationBuilder()

    with pytest.raises(ValueError, match="cannot be negative"):
        builder.build(scenario, -1)

    with pytest.raises(ValueError, match="is not defined in scenario time indices"):
        builder.build(scenario, 5)


def test_source_destination_validation() -> None:
    scenario = create_mock_scenario()
    builder = RoutingContextBuilder()

    with pytest.raises(ValueError, match="source_node_id N99 does not exist"):
        builder.build(scenario, 1, "N99", "N2")

    with pytest.raises(ValueError, match="destination_node_id N99 does not exist"):
        builder.build(scenario, 1, "N1", "N99")


def test_default_candidate_links() -> None:
    scenario = create_mock_scenario()
    context = RoutingContextBuilder().build(scenario, 1, "N1", "N2")

    assert context.candidate_link_ids == ["L1", "L2", "L3"]


def test_explicit_candidate_link_validation() -> None:
    scenario = create_mock_scenario()
    builder = RoutingContextBuilder()

    with pytest.raises(ValueError, match="candidate_link_id L99 does not exist"):
        builder.build(scenario, 1, "N1", "N2", candidate_link_ids=["L1", "L99"])


def test_stable_export_structure() -> None:
    adversarial_trace = AdversarialTrace()
    adversarial_trace.add_jamming_event(JammingEvent("L2", 1, jammed=True))
    adversarial_trace.add_jamming_event(JammingEvent("L1", 1, jammed=True))

    scenario = create_mock_scenario(adv_trace=adversarial_trace)
    context = RoutingContextBuilder().build(
        scenario,
        1,
        "N1",
        "N2",
        ["L2", "L1"],
    )

    exported = context.to_dict()

    assert exported["type"] == "routing_context"
    assert exported["task"]["candidate_link_ids"] == ["L1", "L2"]

    observation_doc = exported["network_observation"]
    assert observation_doc["adversarial_state"]["jammed_links"] == ["L1", "L2"]

    assert exported["metadata"]["builder_name"] == "RoutingContextBuilder"
    assert exported["metadata"]["builder_version"] == "1.0"
    assert exported["metadata"]["has_adversarial_trace"] is True


def test_deterministic_context_generation() -> None:
    scenario = create_mock_scenario()
    builder = RoutingContextBuilder()

    context_a = builder.build(scenario, 0, "N1", "N2", ["L1", "L3"])
    context_b = builder.build(scenario, 0, "N1", "N2", ["L1", "L3"])

    assert context_a.to_dict() == context_b.to_dict()


def test_export_does_not_leak_internal_mutable_references() -> None:
    adversarial_trace = AdversarialTrace()
    adversarial_trace.add_jamming_event(JammingEvent("L1", 1, jammed=True))

    scenario = create_mock_scenario(adv_trace=adversarial_trace)
    context = RoutingContextBuilder().build(scenario, 1, "N1", "N2")

    exported = context.to_dict()
    exported["metadata"]["builder_name"] = "BROKEN"
    exported["task"]["candidate_link_ids"][0] = "BAD"
    exported["network_observation"]["adversarial_state"]["jammed_links"][0] = "BAD"

    exported_again = context.to_dict()

    assert exported_again["metadata"]["builder_name"] == "RoutingContextBuilder"
    assert exported_again["task"]["candidate_link_ids"][0] == "L1"
    assert exported_again["network_observation"]["adversarial_state"]["jammed_links"][0] == "L1"