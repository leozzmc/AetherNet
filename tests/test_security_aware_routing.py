import pytest

from aether_routing_context import NetworkObservation, RoutingContext
from aether_routing_scoring import LinkScore, RoutingScoreReport
from aether_security_routing import SecurityAwareRoutingEngine
from aether_security_signals import LinkSecuritySignal, SecuritySignalReport


def create_mock_context(
    candidates=None,
    scenario="test",
    time=10,
    src="N1",
    dst="N2",
):
    if candidates is None:
        candidates = ["L1", "L2", "L3"]

    return RoutingContext(
        scenario_name=scenario,
        master_seed=42,
        time_index=time,
        source_node_id=src,
        destination_node_id=dst,
        candidate_link_ids=candidates,
        network_observation=NetworkObservation(
            time,
            ["N1", "N2"],
            candidates,
            [],
            {},
            [],
            [],
            [],
            {},
        ),
        metadata={},
    )


def create_mock_score_report(
    scores,
    scenario="test",
    time=10,
    src="N1",
    dst="N2",
):
    return RoutingScoreReport(
        scenario_name=scenario,
        time_index=time,
        source_node_id=src,
        destination_node_id=dst,
        link_scores=scores,
        metadata={
            "scorer_name": "ProbabilisticScorer",
            "scorer_version": "1.0",
            "compromised_node_count": 0,
            "compromised_nodes": [],
        },
    )


def create_mock_signal_report(
    signals,
    scenario="test",
    time=10,
    src="N1",
    dst="N2",
):
    return SecuritySignalReport(
        scenario_name=scenario,
        time_index=time,
        source_node_id=src,
        destination_node_id=dst,
        link_signals=signals,
        node_signals=[],
        summary={},
        metadata={
            "builder_name": "SecuritySignalBuilder",
            "builder_version": "1.0",
        },
    )


def mock_score(link_id, prob):
    return LinkScore(
        link_id=link_id,
        base_score=1.0,
        penalties={},
        total_penalty=max(0.0, 1.0 - prob),
        final_score=prob,
        estimated_success_probability=prob,
        reasons=[],
    )


def mock_signal(link_id, severity, jam=False, drop=False, prob=1.0):
    return LinkSecuritySignal(
        link_id=link_id,
        jammed=jam,
        malicious_drop_risk=drop,
        degraded=False,
        extra_delay_ms=0,
        injected_delay_ms=0,
        estimated_success_probability=prob,
        severity=severity,
        reasons=[],
    )


def test_decision_classification() -> None:
    context = create_mock_context(candidates=["L1", "L2", "L3", "L4", "L5"])

    scores = [
        mock_score("L1", 0.9),
        mock_score("L2", 0.9),
        mock_score("L3", 0.8),
        mock_score("L4", 0.6),
        mock_score("L5", 0.8),
    ]
    signals = [
        mock_signal("L1", "high", prob=0.9),
        mock_signal("L2", "low", jam=True, prob=0.9),
        mock_signal("L3", "low", prob=0.8),
        mock_signal("L4", "low", prob=0.6),
        mock_signal("L5", "medium", prob=0.8),
    ]

    engine = SecurityAwareRoutingEngine()
    decision = engine.build_decision(
        context,
        create_mock_score_report(scores),
        create_mock_signal_report(signals),
    )

    decision_by_link = {item.link_id: item.decision for item in decision.link_decisions}
    assert decision_by_link["L1"] == "avoid"
    assert decision_by_link["L2"] == "avoid"
    assert decision_by_link["L3"] == "preferred"
    assert decision_by_link["L4"] == "allowed"
    assert decision_by_link["L5"] == "allowed"


def test_recommended_link_fallback() -> None:
    engine = SecurityAwareRoutingEngine()
    context = create_mock_context(candidates=["L1", "L2"])

    scores_a = [mock_score("L1", 0.9), mock_score("L2", 0.6)]
    signals_a = [
        mock_signal("L1", "low", prob=0.9),
        mock_signal("L2", "low", prob=0.6),
    ]
    decision_a = engine.build_decision(
        context,
        create_mock_score_report(scores_a),
        create_mock_signal_report(signals_a),
    )
    assert decision_a.recommended_link_ids == ["L1"]

    scores_b = [mock_score("L1", 0.2), mock_score("L2", 0.6)]
    signals_b = [
        mock_signal("L1", "high", prob=0.2),
        mock_signal("L2", "low", prob=0.6),
    ]
    decision_b = engine.build_decision(
        context,
        create_mock_score_report(scores_b),
        create_mock_signal_report(signals_b),
    )
    assert decision_b.recommended_link_ids == ["L2"]

    scores_c = [mock_score("L1", 0.1), mock_score("L2", 0.1)]
    signals_c = [
        mock_signal("L1", "high", prob=0.1),
        mock_signal("L2", "high", prob=0.1),
    ]
    decision_c = engine.build_decision(
        context,
        create_mock_score_report(scores_c),
        create_mock_signal_report(signals_c),
    )
    assert decision_c.recommended_link_ids == []
    assert set(decision_c.avoided_link_ids) == {"L1", "L2"}


def test_alignment_validation() -> None:
    engine = SecurityAwareRoutingEngine()

    context_a = create_mock_context(scenario="A")
    score_b = create_mock_score_report([], scenario="B")
    signal_a = create_mock_signal_report([], scenario="A")

    with pytest.raises(ValueError, match="Mismatched scenario_name"):
        engine.build_decision(context_a, score_b, signal_a)

    context_t1 = create_mock_context(time=1)
    score_t1 = create_mock_score_report([], time=1)
    signal_t2 = create_mock_signal_report([], time=2)

    with pytest.raises(ValueError, match="Mismatched time_index"):
        engine.build_decision(context_t1, score_t1, signal_t2)


def test_candidate_membership_validation() -> None:
    engine = SecurityAwareRoutingEngine()
    context = create_mock_context(candidates=["L1"])

    score_bad = create_mock_score_report([mock_score("L99", 1.0)])
    signal_ok = create_mock_signal_report([mock_signal("L1", "low")])
    with pytest.raises(ValueError, match="Scored link L99 is not a valid candidate"):
        engine.build_decision(context, score_bad, signal_ok)

    score_ok = create_mock_score_report([mock_score("L1", 1.0)])
    signal_bad = create_mock_signal_report([mock_signal("L88", "low")])
    with pytest.raises(ValueError, match="Signaled link L88 is not a valid candidate"):
        engine.build_decision(context, score_ok, signal_bad)


def test_candidate_coverage_validation() -> None:
    engine = SecurityAwareRoutingEngine()
    context = create_mock_context(candidates=["L1", "L2"])

    score_missing = create_mock_score_report([mock_score("L1", 1.0)])
    signal_full = create_mock_signal_report(
        [mock_signal("L1", "low"), mock_signal("L2", "low")]
    )
    with pytest.raises(ValueError, match="Missing scored links"):
        engine.build_decision(context, score_missing, signal_full)

    score_full = create_mock_score_report(
        [mock_score("L1", 1.0), mock_score("L2", 1.0)]
    )
    signal_missing = create_mock_signal_report([mock_signal("L1", "low")])
    with pytest.raises(ValueError, match="Missing signaled links"):
        engine.build_decision(context, score_full, signal_missing)


def test_export_mutation_safety_and_ordering() -> None:
    engine = SecurityAwareRoutingEngine()
    context = create_mock_context(candidates=["L2", "L1"])
    score_report = create_mock_score_report(
        [mock_score("L2", 1.0), mock_score("L1", 1.0)]
    )
    signal_report = create_mock_signal_report(
        [mock_signal("L2", "low"), mock_signal("L1", "low")]
    )

    decision = engine.build_decision(context, score_report, signal_report)
    exported = decision.to_dict()

    assert exported["recommendation"]["recommended_link_ids"] == ["L1", "L2"]
    assert exported["link_decisions"][0]["link_id"] == "L1"

    exported["recommendation"]["recommended_link_ids"].append("HACKED")
    exported["metadata"]["engine_name"] = "BROKEN"

    exported_again = decision.to_dict()
    assert "HACKED" not in exported_again["recommendation"]["recommended_link_ids"]
    assert exported_again["metadata"]["engine_name"] == "SecurityAwareRoutingEngine"


def test_deterministic_decision_generation() -> None:
    context = create_mock_context(candidates=["L1"])
    score_report = create_mock_score_report([mock_score("L1", 0.5)])
    signal_report = create_mock_signal_report([mock_signal("L1", "medium", prob=0.5)])

    engine_a = SecurityAwareRoutingEngine()
    engine_b = SecurityAwareRoutingEngine()

    assert (
        engine_a.build_decision(context, score_report, signal_report).to_dict()
        == engine_b.build_decision(context, score_report, signal_report).to_dict()
    )