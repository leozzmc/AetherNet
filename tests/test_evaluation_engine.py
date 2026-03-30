import pytest

from aether_evaluation import EvaluationCase, PolicyEvaluationEngine
from aether_routing_context import NetworkObservation, RoutingContext
from aether_routing_scoring import ProbabilisticScorer
from aether_scenarios import GeneratedScenario


def create_mock_scenario(name="test_scene") -> GeneratedScenario:
    return GeneratedScenario(
        scenario_name=name,
        master_seed=42,
        node_ids=["N1", "N2", "N3"],
        link_ids=["L1", "L2", "L3"],
        time_indices=[0, 1, 2],
        metadata={"mock": True},
    )


def create_mock_context(
    name="test_scene",
    candidate_links=None,
    degraded=None,
    compromised_nodes=None,
) -> RoutingContext:
    if candidate_links is None:
        candidate_links = ["L1", "L2", "L3"]
    if degraded is None:
        degraded = []
    if compromised_nodes is None:
        compromised_nodes = []

    observation = NetworkObservation(
        time_index=1,
        node_ids=["N1", "N2", "N3"],
        link_ids=["L1", "L2", "L3"],
        degraded_links=degraded,
        extra_delay_ms_by_link={},
        jammed_links=[],
        malicious_drop_links=[],
        compromised_nodes=compromised_nodes,
        injected_delay_ms_by_link={},
    )

    return RoutingContext(
        scenario_name=name,
        master_seed=42,
        time_index=1,
        source_node_id="N1",
        destination_node_id="N2",
        candidate_link_ids=candidate_links,
        network_observation=observation,
        metadata={"mock": True},
    )


def test_empty_input_handling() -> None:
    engine = PolicyEvaluationEngine()
    scorer = ProbabilisticScorer()

    results, summary = engine.evaluate_cases([], scorer)

    assert results == []
    assert summary.case_count == 0
    assert summary.total_link_score_count == 0
    assert summary.average_final_score == 0.0
    assert summary.average_success_probability == 0.0
    assert summary.min_final_score == 0.0
    assert summary.max_final_score == 0.0
    assert summary.compromised_node_case_count == 0


def test_stable_case_ordering() -> None:
    scenario = create_mock_scenario()
    context = create_mock_context()

    case_z = EvaluationCase("case_Z", scenario, context)
    case_a = EvaluationCase("case_A", scenario, context)

    engine = PolicyEvaluationEngine()
    scorer = ProbabilisticScorer()

    results, _ = engine.evaluate_cases([case_z, case_a], scorer)

    assert len(results) == 2
    assert results[0].case_id == "case_A"
    assert results[1].case_id == "case_Z"


def test_aggregation_correctness() -> None:
    scenario = create_mock_scenario()

    context_1 = create_mock_context(
        candidate_links=["L1", "L2"],
        degraded=["L1"],
    )
    case_1 = EvaluationCase("case_1", scenario, context_1)

    context_2 = create_mock_context(candidate_links=["L1"])
    case_2 = EvaluationCase("case_2", scenario, context_2)

    engine = PolicyEvaluationEngine()
    scorer = ProbabilisticScorer()

    _, summary = engine.evaluate_cases([case_1, case_2], scorer)

    assert summary.case_count == 2
    assert summary.total_link_score_count == 3
    assert summary.min_final_score == 0.85
    assert summary.max_final_score == 1.0

    expected_average = (0.85 + 1.0 + 1.0) / 3
    assert summary.average_final_score == pytest.approx(expected_average)
    assert summary.average_success_probability == pytest.approx(expected_average)


def test_compromised_node_case_counting() -> None:
    scenario = create_mock_scenario()

    context_clean = create_mock_context(compromised_nodes=[])
    context_comp_1 = create_mock_context(compromised_nodes=["N1"])
    context_comp_2 = create_mock_context(compromised_nodes=["N2", "N3"])

    case_1 = EvaluationCase("C1", scenario, context_clean)
    case_2 = EvaluationCase("C2", scenario, context_comp_1)
    case_3 = EvaluationCase("C3", scenario, context_comp_2)

    engine = PolicyEvaluationEngine()
    scorer = ProbabilisticScorer()

    _, summary = engine.evaluate_cases([case_1, case_2, case_3], scorer)

    assert summary.case_count == 3
    assert summary.compromised_node_case_count == 2


def test_stable_export_structure() -> None:
    scenario = create_mock_scenario()
    context = create_mock_context(candidate_links=["L1"])
    case = EvaluationCase("case_A", scenario, context)

    engine = PolicyEvaluationEngine()
    scorer = ProbabilisticScorer()

    results, summary = engine.evaluate_cases([case], scorer)

    case_doc = case.to_dict()
    assert case_doc["case_id"] == "case_A"
    assert "routing_context" not in case_doc

    result_doc = results[0].to_dict()
    assert result_doc["case_id"] == "case_A"
    assert result_doc["metadata"]["scorer_name"] == "ProbabilisticScorer"
    assert result_doc["metadata"]["scorer_version"] == "1.0"
    assert result_doc["metadata"]["candidate_link_count"] == 1
    assert "routing_score_report" in result_doc

    summary_doc = summary.to_dict()
    assert summary_doc["type"] == "evaluation_summary"
    assert summary_doc["metrics"]["case_count"] == 1
    assert summary_doc["metrics"]["total_link_score_count"] == 1
    assert summary_doc["metadata"]["engine_name"] == "PolicyEvaluationEngine"
    assert summary_doc["metadata"]["engine_version"] == "1.0"


def test_deterministic_evaluation() -> None:
    scenario = create_mock_scenario()
    context = create_mock_context()
    case = EvaluationCase("C1", scenario, context)

    engine_1 = PolicyEvaluationEngine()
    engine_2 = PolicyEvaluationEngine()
    scorer = ProbabilisticScorer()

    results_1, summary_1 = engine_1.evaluate_cases([case], scorer)
    results_2, summary_2 = engine_2.evaluate_cases([case], scorer)

    assert [result.to_dict() for result in results_1] == [
        result.to_dict() for result in results_2
    ]
    assert summary_1.to_dict() == summary_2.to_dict()


def test_case_id_validation() -> None:
    scenario = create_mock_scenario()
    context = create_mock_context()

    with pytest.raises(ValueError, match="case_id must be a non-empty string"):
        EvaluationCase("   ", scenario, context)


def test_export_does_not_leak_internal_mutable_references() -> None:
    scenario = create_mock_scenario()
    context = create_mock_context(candidate_links=["L1"], compromised_nodes=["N2"])
    case = EvaluationCase("case_mutation", scenario, context)

    engine = PolicyEvaluationEngine()
    scorer = ProbabilisticScorer()

    results, summary = engine.evaluate_cases([case], scorer)

    result_export = results[0].to_dict()
    result_export["metadata"]["scorer_name"] = "BROKEN"
    result_export["routing_score_report"]["metadata"]["scorer_name"] = "BROKEN"

    summary_export = summary.to_dict()
    summary_export["metadata"]["engine_name"] = "BROKEN"
    summary_export["scorer"]["scorer_name"] = "BROKEN"

    result_export_again = results[0].to_dict()
    summary_export_again = summary.to_dict()

    assert result_export_again["metadata"]["scorer_name"] == "ProbabilisticScorer"
    assert (
        result_export_again["routing_score_report"]["metadata"]["scorer_name"]
        == "ProbabilisticScorer"
    )
    assert summary_export_again["metadata"]["engine_name"] == "PolicyEvaluationEngine"
    assert summary_export_again["scorer"]["scorer_name"] == "ProbabilisticScorer"