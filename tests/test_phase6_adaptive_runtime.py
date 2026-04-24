import pytest

from aether_phase6_runtime.adaptive import (
    AdaptivePhase6Adapter,
    AdaptiveRuntimeMode,
    AdaptiveRuntimePolicy,
)
from aether_phase6_runtime.metrics import RoutingMetricsSummary
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
        scenario_name="adaptive_test",
        master_seed=42,
        time_index=10,
        source_node_id="N1",
        destination_node_id="N2",
        candidate_link_ids=candidates,
        network_observation=observation,
        metadata={},
    )


def mock_summary(
    average_filtered: float,
    preferred_ratio: float,
) -> RoutingMetricsSummary:
    return RoutingMetricsSummary(
        total_decisions=100,
        preferred_ratio=preferred_ratio,
        allowed_ratio=max(0.0, 1.0 - preferred_ratio),
        average_filtered=average_filtered,
    )


@pytest.fixture
def adaptive_adapter() -> AdaptivePhase6Adapter:
    return AdaptivePhase6Adapter()


def test_policy_selects_conservative_when_heavy_filtering() -> None:
    summary = mock_summary(average_filtered=2.5, preferred_ratio=0.5)

    assert AdaptiveRuntimePolicy.select_mode(summary) == AdaptiveRuntimeMode.CONSERVATIVE


def test_policy_selects_aggressive_when_healthy() -> None:
    summary = mock_summary(average_filtered=0.5, preferred_ratio=0.8)

    assert AdaptiveRuntimePolicy.select_mode(summary) == AdaptiveRuntimeMode.AGGRESSIVE


def test_policy_selects_balanced_in_normal_conditions() -> None:
    summary = mock_summary(average_filtered=1.0, preferred_ratio=0.5)

    assert AdaptiveRuntimePolicy.select_mode(summary) == AdaptiveRuntimeMode.BALANCED


def test_conservative_returns_only_preferred_if_available(
    adaptive_adapter: AdaptivePhase6Adapter,
) -> None:
    context = create_mock_context(
        candidates=["L1", "L2"],
        degraded_links=["L2"],
    )
    summary = mock_summary(average_filtered=2.5, preferred_ratio=0.5)

    result = adaptive_adapter.apply_adaptive_decision(
        context,
        ["L1", "L2"],
        summary,
    )

    assert result == ["L1"]


def test_conservative_returns_allowed_if_no_preferred(
    adaptive_adapter: AdaptivePhase6Adapter,
) -> None:
    context = create_mock_context(
        candidates=["L1", "L2"],
        degraded_links=["L1", "L2"],
    )
    summary = mock_summary(average_filtered=2.5, preferred_ratio=0.5)

    result = adaptive_adapter.apply_adaptive_decision(
        context,
        ["L1", "L2"],
        summary,
    )

    assert result == ["L1", "L2"]


def test_balanced_hoists_preferred_and_preserves_allowed(
    adaptive_adapter: AdaptivePhase6Adapter,
) -> None:
    context = create_mock_context(
        candidates=["L1", "L2"],
        degraded_links=["L2"],
    )
    summary = mock_summary(average_filtered=1.0, preferred_ratio=0.5)

    result = adaptive_adapter.apply_adaptive_decision(
        context,
        ["L2", "L1"],
        summary,
    )

    assert result == ["L1", "L2"]


def test_aggressive_preserves_original_safe_order(
    adaptive_adapter: AdaptivePhase6Adapter,
) -> None:
    context = create_mock_context(
        candidates=["L1", "L2", "L3"],
        degraded_links=["L2"],
        jammed_links=["L3"],
    )
    summary = mock_summary(average_filtered=0.0, preferred_ratio=0.9)

    result = adaptive_adapter.apply_adaptive_decision(
        context,
        ["L2", "L3", "L1"],
        summary,
    )

    assert result == ["L2", "L1"]


def test_avoid_is_never_returned_in_any_mode(
    adaptive_adapter: AdaptivePhase6Adapter,
) -> None:
    context = create_mock_context(
        candidates=["L1", "L2", "L3"],
        jammed_links=["L2"],
        degraded_links=["L3"],
    )

    summaries = [
        mock_summary(average_filtered=2.5, preferred_ratio=0.5),
        mock_summary(average_filtered=1.0, preferred_ratio=0.5),
        mock_summary(average_filtered=0.0, preferred_ratio=0.9),
    ]

    for summary in summaries:
        result = adaptive_adapter.apply_adaptive_decision(
            context,
            ["L1", "L2", "L3"],
            summary,
        )
        assert "L2" not in result


def test_deterministic_execution(
    adaptive_adapter: AdaptivePhase6Adapter,
) -> None:
    context = create_mock_context(
        candidates=["L1", "L2"],
        degraded_links=["L2"],
    )
    summary = mock_summary(average_filtered=2.5, preferred_ratio=0.5)

    run_1 = adaptive_adapter.apply_adaptive_decision(context, ["L1", "L2"], summary)
    run_2 = adaptive_adapter.apply_adaptive_decision(context, ["L1", "L2"], summary)

    assert run_1 == run_2


def test_empty_candidates_handling(
    adaptive_adapter: AdaptivePhase6Adapter,
) -> None:
    context = create_mock_context(candidates=[])
    summary = mock_summary(average_filtered=1.0, preferred_ratio=0.5)

    result = adaptive_adapter.apply_adaptive_decision(context, [], summary)

    assert result == []