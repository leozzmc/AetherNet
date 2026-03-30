from aether_routing_context import NetworkObservation, RoutingContext
from aether_routing_scoring import ProbabilisticScorer


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
        compromised_nodes = []

    observation = NetworkObservation(
        time_index=10,
        node_ids=["N1", "N2", "N3"],
        link_ids=["L1", "L2", "L3", "L4"],
        degraded_links=degraded,
        extra_delay_ms_by_link=extra_delay,
        jammed_links=jammed,
        malicious_drop_links=malicious_drop,
        compromised_nodes=compromised_nodes,
        injected_delay_ms_by_link=injected_delay,
    )

    return RoutingContext(
        scenario_name="scoring_test",
        master_seed=42,
        time_index=10,
        source_node_id="N1",
        destination_node_id="N2",
        candidate_link_ids=candidate_links,
        network_observation=observation,
        metadata={"mock": True},
    )


def test_clean_link_score() -> None:
    context = create_mock_context(candidate_links=["L1"])
    scorer = ProbabilisticScorer()

    report = scorer.score(context)
    score = report.link_scores[0]

    assert score.link_id == "L1"
    assert score.base_score == 1.0
    assert score.penalties == {}
    assert score.total_penalty == 0.0
    assert score.reasons == []
    assert score.final_score == 1.0
    assert score.estimated_success_probability == 1.0


def test_degraded_jammed_malicious_drop_penalties() -> None:
    context = create_mock_context(
        candidate_links=["L1", "L2", "L3"],
        degraded=["L1"],
        jammed=["L2"],
        malicious_drop=["L3"],
    )
    scorer = ProbabilisticScorer()
    report = scorer.score(context)

    score_l1 = next(score for score in report.link_scores if score.link_id == "L1")
    assert score_l1.penalties["degraded_link"] == 0.15
    assert score_l1.total_penalty == 0.15
    assert score_l1.final_score == 0.85
    assert "degraded_link" in score_l1.reasons

    score_l2 = next(score for score in report.link_scores if score.link_id == "L2")
    assert score_l2.penalties["jammed_link"] == 0.35
    assert score_l2.total_penalty == 0.35
    assert score_l2.final_score == 0.65
    assert "jammed_link" in score_l2.reasons

    score_l3 = next(score for score in report.link_scores if score.link_id == "L3")
    assert score_l3.penalties["malicious_drop_risk"] == 0.40
    assert score_l3.total_penalty == 0.40
    assert score_l3.final_score == 0.60
    assert "malicious_drop_risk" in score_l3.reasons


def test_delay_penalties_and_bounds() -> None:
    context = create_mock_context(
        candidate_links=["L1", "L2", "L3", "L4"],
        extra_delay={"L1": 100, "L2": 5000},
        injected_delay={"L3": 150, "L4": 9999},
    )
    scorer = ProbabilisticScorer()
    report = scorer.score(context)

    score_l1 = next(score for score in report.link_scores if score.link_id == "L1")
    assert score_l1.penalties["extra_delay_penalty"] == 0.1
    assert "extra_delay_ms=100" in score_l1.reasons

    score_l2 = next(score for score in report.link_scores if score.link_id == "L2")
    assert score_l2.penalties["extra_delay_penalty"] == 0.2

    score_l3 = next(score for score in report.link_scores if score.link_id == "L3")
    assert score_l3.penalties["injected_delay_penalty"] == 0.15
    assert "injected_delay_ms=150" in score_l3.reasons

    score_l4 = next(score for score in report.link_scores if score.link_id == "L4")
    assert score_l4.penalties["injected_delay_penalty"] == 0.25


def test_score_clamping() -> None:
    context = create_mock_context(
        candidate_links=["L1"],
        degraded=["L1"],
        jammed=["L1"],
        malicious_drop=["L1"],
        injected_delay={"L1": 9000},
    )
    scorer = ProbabilisticScorer()
    report = scorer.score(context)

    score = report.link_scores[0]
    assert score.total_penalty == 1.15
    assert score.final_score == 0.0
    assert score.estimated_success_probability == 0.0


def test_compromised_nodes_stay_in_metadata_only() -> None:
    context = create_mock_context(
        candidate_links=["L1"],
        compromised_nodes=["N1", "N3"],
    )
    scorer = ProbabilisticScorer()
    report = scorer.score(context)

    score = report.link_scores[0]
    assert score.final_score == 1.0
    assert score.penalties == {}
    assert score.total_penalty == 0.0

    assert report.metadata["compromised_node_count"] == 2
    assert report.metadata["compromised_nodes"] == ["N1", "N3"]


def test_stable_export_ordering() -> None:
    context = create_mock_context(
        candidate_links=["L2", "L1"],
        degraded=["L1"],
        injected_delay={"L1": 50},
    )
    scorer = ProbabilisticScorer()
    report = scorer.score(context)

    exported = report.to_dict()

    assert exported["link_scores"][0]["link_id"] == "L1"
    assert exported["link_scores"][1]["link_id"] == "L2"

    score_l1 = exported["link_scores"][0]
    assert list(score_l1["penalties"].keys()) == [
        "degraded_link",
        "injected_delay_penalty",
    ]
    assert score_l1["reasons"] == ["degraded_link", "injected_delay_ms=50"]


def test_deterministic_scoring() -> None:
    context = create_mock_context(
        candidate_links=["L1", "L3"],
        jammed=["L1"],
        extra_delay={"L3": 250},
    )
    scorer = ProbabilisticScorer()

    report_a = scorer.score(context)
    report_b = scorer.score(context)

    assert report_a.to_dict() == report_b.to_dict()


def test_export_does_not_leak_internal_mutable_references() -> None:
    context = create_mock_context(
        candidate_links=["L1"],
        jammed=["L1"],
        compromised_nodes=["N2"],
    )
    scorer = ProbabilisticScorer()
    report = scorer.score(context)

    exported = report.to_dict()
    exported["metadata"]["scorer_name"] = "BROKEN"
    exported["metadata"]["compromised_nodes"][0] = "BAD"
    exported["link_scores"][0]["reasons"][0] = "BAD"
    exported["link_scores"][0]["penalties"]["jammed_link"] = 999.0

    exported_again = report.to_dict()

    assert exported_again["metadata"]["scorer_name"] == "ProbabilisticScorer"
    assert exported_again["metadata"]["compromised_nodes"] == ["N2"]
    assert exported_again["link_scores"][0]["reasons"] == ["jammed_link"]
    assert exported_again["link_scores"][0]["penalties"]["jammed_link"] == 0.35