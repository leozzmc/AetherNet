import pytest

from aether_routing_context import NetworkObservation, RoutingContext
from aether_routing_scoring import LinkScore, RoutingScoreReport
from aether_security_signals import SecuritySignalBuilder


def create_mock_context(
    candidate_links=None,
    degraded=None,
    jammed=None,
    malicious_drop=None,
    extra_delay=None,
    injected_delay=None,
    compromised_nodes=None,
) -> RoutingContext:
    if candidate_links is None:
        candidate_links = ["L1", "L2", "L3"]
    if degraded is None:
        degraded = []
    if jammed is None:
        jammed = []
    if malicious_drop is None:
        malicious_drop = []
    if extra_delay is None:
        extra_delay = {}
    if injected_delay is None:
        injected_delay = {}
    if compromised_nodes is None:
        compromised_nodes = ["N3"]

    observation = NetworkObservation(
        time_index=10,
        node_ids=["N1", "N2", "N3"],
        link_ids=["L1", "L2", "L3"],
        degraded_links=degraded,
        extra_delay_ms_by_link=extra_delay,
        jammed_links=jammed,
        malicious_drop_links=malicious_drop,
        compromised_nodes=compromised_nodes,
        injected_delay_ms_by_link=injected_delay,
    )
    return RoutingContext(
        scenario_name="sig_test",
        master_seed=42,
        time_index=10,
        source_node_id="N1",
        destination_node_id="N2",
        candidate_link_ids=candidate_links,
        network_observation=observation,
        metadata={},
    )


def create_mock_score_report(
    scores: list[LinkScore],
    scenario_name: str = "sig_test",
    time_index: int = 10,
    source_node_id: str = "N1",
    destination_node_id: str = "N2",
) -> RoutingScoreReport:
    return RoutingScoreReport(
        scenario_name=scenario_name,
        time_index=time_index,
        source_node_id=source_node_id,
        destination_node_id=destination_node_id,
        link_scores=scores,
        metadata={
            "scorer_name": "ProbabilisticScorer",
            "scorer_version": "1.0",
            "compromised_node_count": 0,
            "compromised_nodes": [],
        },
    )


def create_mock_link_score(link_id: str, prob: float) -> LinkScore:
    return LinkScore(
        link_id=link_id,
        base_score=1.0,
        penalties={},
        total_penalty=max(0.0, 1.0 - prob),
        final_score=prob,
        estimated_success_probability=prob,
        reasons=[],
    )


def test_link_severity_classification() -> None:
    context = create_mock_context(
        candidate_links=["L1", "L2", "L3", "L4", "L5", "L6"],
        jammed=["L1"],
        malicious_drop=["L2"],
        degraded=["L3"],
    )
    scores = [
        create_mock_link_score("L1", 1.0),
        create_mock_link_score("L2", 1.0),
        create_mock_link_score("L3", 1.0),
        create_mock_link_score("L4", 0.35),
        create_mock_link_score("L5", 0.60),
        create_mock_link_score("L6", 1.0),
    ]
    report = create_mock_score_report(scores)

    signal_report = SecuritySignalBuilder().build(context, report)
    signals = {signal.link_id: signal for signal in signal_report.link_signals}

    assert signals["L1"].severity == "high"
    assert "jammed_link" in signals["L1"].reasons

    assert signals["L2"].severity == "high"
    assert "malicious_drop_risk" in signals["L2"].reasons

    assert signals["L3"].severity == "medium"
    assert "degraded_link" in signals["L3"].reasons

    assert signals["L4"].severity == "high"
    assert "estimated_success_probability<0.40" in signals["L4"].reasons

    assert signals["L5"].severity == "medium"
    assert "estimated_success_probability<0.75" in signals["L5"].reasons

    assert signals["L6"].severity == "low"


def test_node_severity_classification() -> None:
    context = create_mock_context(compromised_nodes=["N3"])
    scores = [create_mock_link_score("L1", 1.0)]
    report = create_mock_score_report(scores)

    signal_report = SecuritySignalBuilder().build(context, report)
    nodes = {signal.node_id: signal for signal in signal_report.node_signals}

    assert nodes["N1"].severity == "low"
    assert nodes["N2"].severity == "low"
    assert nodes["N3"].severity == "high"
    assert "compromised_node" in nodes["N3"].reasons


def test_summary_correctness() -> None:
    context = create_mock_context(
        candidate_links=["L1", "L2"],
        jammed=["L1"],
        compromised_nodes=["N1", "N2"],
    )
    scores = [
        create_mock_link_score("L1", 1.0),
        create_mock_link_score("L2", 1.0),
    ]
    report = create_mock_score_report(scores)

    signal_report = SecuritySignalBuilder().build(context, report)
    summary = signal_report.summary

    assert summary["high_severity_link_count"] == 1
    assert summary["medium_severity_link_count"] == 0
    assert summary["low_severity_link_count"] == 1
    assert summary["compromised_node_count"] == 2
    assert summary["jammed_link_count"] == 1
    assert summary["malicious_drop_link_count"] == 0


def test_validation_for_mismatched_links() -> None:
    context = create_mock_context(candidate_links=["L1"])
    scores = [create_mock_link_score("L99", 1.0)]
    report = create_mock_score_report(scores)

    with pytest.raises(ValueError, match="is not a valid candidate"):
        SecuritySignalBuilder().build(context, report)


def test_validation_for_context_score_report_alignment() -> None:
    context = create_mock_context(candidate_links=["L1"])
    scores = [create_mock_link_score("L1", 1.0)]

    report = create_mock_score_report(scores, time_index=999)

    with pytest.raises(ValueError, match="time_index do not match"):
        SecuritySignalBuilder().build(context, report)


def test_export_mutation_safety() -> None:
    context = create_mock_context(compromised_nodes=["N3"])
    scores = [create_mock_link_score("L1", 1.0)]
    report = create_mock_score_report(scores)

    signal_report = SecuritySignalBuilder().build(context, report)
    exported = signal_report.to_dict()

    exported["node_signals"][2]["severity"] = "HACKED"
    exported["summary"]["jammed_link_count"] = 999
    exported["metadata"]["builder_name"] = "BROKEN"

    exported_again = signal_report.to_dict()
    assert exported_again["node_signals"][2]["severity"] == "high"
    assert exported_again["summary"]["jammed_link_count"] == 0
    assert exported_again["metadata"]["builder_name"] == "SecuritySignalBuilder"


def test_deterministic_signal_generation() -> None:
    context = create_mock_context(
        jammed=["L1"],
        extra_delay={"L2": 50},
    )
    scores = [
        create_mock_link_score("L1", 0.1),
        create_mock_link_score("L2", 0.8),
        create_mock_link_score("L3", 1.0),
    ]
    report = create_mock_score_report(scores)

    builder_a = SecuritySignalBuilder()
    builder_b = SecuritySignalBuilder()

    assert builder_a.build(context, report).to_dict() == builder_b.build(context, report).to_dict()


def test_stable_export_ordering() -> None:
    context = create_mock_context(
        candidate_links=["L2", "L1"],
        jammed=["L2"],
        compromised_nodes=["N2"],
    )
    scores = [
        create_mock_link_score("L2", 1.0),
        create_mock_link_score("L1", 1.0),
    ]
    report = create_mock_score_report(scores)

    exported = SecuritySignalBuilder().build(context, report).to_dict()

    assert exported["link_signals"][0]["link_id"] == "L1"
    assert exported["link_signals"][1]["link_id"] == "L2"
    assert exported["node_signals"][0]["node_id"] == "N1"
    assert exported["node_signals"][1]["node_id"] == "N2"
    assert exported["node_signals"][2]["node_id"] == "N3"