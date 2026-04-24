import pytest

from aether_phase6_runtime.comparison import (
    PolicyComparisonCase,
    PolicyComparisonRunner,
)
from aether_routing_context import NetworkObservation, RoutingContext


def create_mock_context(
    candidates: list[str],
    jammed_links: list[str] | None = None,
    degraded_links: list[str] | None = None,
) -> RoutingContext:
    if jammed_links is None:
        jammed_links = []
    if degraded_links is None:
        degraded_links = []

    observation = NetworkObservation(
        time_index=10,
        node_ids=["N1", "N2", "N3"],
        link_ids=["L1", "L2", "L3", "L4"],
        degraded_links=degraded_links,
        extra_delay_ms_by_link={},
        jammed_links=jammed_links,
        malicious_drop_links=[],
        compromised_nodes=[],
        injected_delay_ms_by_link={},
    )

    return RoutingContext(
        scenario_name="comparison_test",
        master_seed=42,
        time_index=10,
        source_node_id="N1",
        destination_node_id="N2",
        candidate_link_ids=candidates,
        network_observation=observation,
        metadata={},
    )


@pytest.fixture
def runner() -> PolicyComparisonRunner:
    return PolicyComparisonRunner()


def test_policy_comparison_case_validation() -> None:
    context = create_mock_context(["L1"])

    with pytest.raises(ValueError, match="case_id must be a non-empty string"):
        PolicyComparisonCase(
            case_id="   ",
            context=context,
            candidate_link_ids=["L1"],
        )


def test_deterministic_comparison_output(
    runner: PolicyComparisonRunner,
) -> None:
    context = create_mock_context(["L1", "L2"], degraded_links=["L2"])

    case_a = PolicyComparisonCase("case1", context, ["L1", "L2"])
    case_b = PolicyComparisonCase("case1", context, ["L1", "L2"])

    result_a = runner.run_case(case_a)
    result_b = runner.run_case(case_b)

    assert result_a.to_dict() == result_b.to_dict()


def test_comparison_fields_and_conservative_stricter(
    runner: PolicyComparisonRunner,
) -> None:
    context = create_mock_context(["L1", "L2"], degraded_links=["L2"])
    case = PolicyComparisonCase("case2", context, ["L1", "L2"])

    result = runner.run_case(case)

    assert result.baseline_candidates == ["L1", "L2"]
    assert result.balanced_candidates == ["L1", "L2"]
    assert result.conservative_candidates == ["L1"]
    assert result.aggressive_candidates == ["L1", "L2"]

    assert len(result.conservative_candidates) < len(result.balanced_candidates)


def test_aggressive_preserves_original_safe_order(
    runner: PolicyComparisonRunner,
) -> None:
    context = create_mock_context(["L1", "L2"], degraded_links=["L2"])
    case = PolicyComparisonCase("case3", context, ["L2", "L1"])

    result = runner.run_case(case)

    assert result.baseline_candidates == ["L1", "L2"]
    assert result.balanced_candidates == ["L1", "L2"]
    assert result.aggressive_candidates == ["L2", "L1"]


def test_avoid_links_never_appear(
    runner: PolicyComparisonRunner,
) -> None:
    context = create_mock_context(
        ["L1", "L2", "L3"],
        jammed_links=["L2"],
    )
    case = PolicyComparisonCase("case4", context, ["L1", "L2", "L3"])

    result = runner.run_case(case)

    for candidates in [
        result.baseline_candidates,
        result.conservative_candidates,
        result.balanced_candidates,
        result.aggressive_candidates,
    ]:
        assert "L2" not in candidates


def test_empty_candidate_list(
    runner: PolicyComparisonRunner,
) -> None:
    context = create_mock_context([])
    case = PolicyComparisonCase("case5", context, [])

    result = runner.run_case(case)

    assert result.baseline_candidates == []
    assert result.conservative_candidates == []
    assert result.balanced_candidates == []
    assert result.aggressive_candidates == []
    assert result.metadata["baseline_count"] == 0


def test_to_dict_mutation_safety(
    runner: PolicyComparisonRunner,
) -> None:
    context = create_mock_context(["L1"])
    case = PolicyComparisonCase("case6", context, ["L1"])

    result = runner.run_case(case)
    exported = result.to_dict()

    exported["baseline_candidates"].append("HACK")
    exported["metadata"]["runner_name"] = "HACKED"

    exported_again = result.to_dict()
    assert "HACK" not in exported_again["baseline_candidates"]
    assert exported_again["metadata"]["runner_name"] == "PolicyComparisonRunner"


def test_to_dict_schema_is_stable(
    runner: PolicyComparisonRunner,
) -> None:
    context = create_mock_context(["L1"])
    case = PolicyComparisonCase("case7", context, ["L1"])

    result = runner.run_case(case).to_dict()

    assert result["type"] == "phase6_policy_comparison_result"
    assert result["version"] == "1.0"
    assert "baseline_candidates" in result
    assert "conservative_candidates" in result
    assert "balanced_candidates" in result
    assert "aggressive_candidates" in result
    assert result["metadata"]["runner_name"] == "PolicyComparisonRunner"
    assert result["metadata"]["runner_version"] == "1.0"