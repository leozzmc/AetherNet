import pytest

from aether_routing_context import NetworkObservation, RoutingContext
from aether_phase6_runtime import ENABLE_PHASE6_RUNTIME, Phase6DecisionAdapter
import aether_phase6_runtime.config as p6_config


# --- Mocks for Isolation ---

def create_mock_context(
    candidates: list[str],
    jammed_links: list[str] = None,
    degraded_links: list[str] = None,
) -> RoutingContext:

    if jammed_links is None:
        jammed_links = []

    if degraded_links is None:
        degraded_links = []

    obs = NetworkObservation(
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
        scenario_name="runtime_bridge_test",
        master_seed=42,
        time_index=10,
        source_node_id="N1",
        destination_node_id="N2",
        candidate_link_ids=candidates,
        network_observation=obs,
        metadata={},
    )


@pytest.fixture
def adapter() -> Phase6DecisionAdapter:
    return Phase6DecisionAdapter()


# --- Tests ---

def test_phase6_filters_avoid_links(adapter: Phase6DecisionAdapter) -> None:
    """Test 1: Verify that links marked as 'avoid' (e.g., jammed) are filtered out."""
    # L2 is jammed, so Phase-6 decision will mark it as 'avoid'
    context = create_mock_context(candidates=["L1", "L2", "L3"], jammed_links=["L2"])
    
    filtered = adapter.filter_candidates(context, ["L1", "L2", "L3"])
    
    # L2 should be removed, L1 and L3 preserved
    assert filtered == ["L1", "L3"]


def test_feature_flag_disabled_by_default() -> None:
    """Test 2: Verify the feature flag defaults to False to protect legacy tests."""
    assert ENABLE_PHASE6_RUNTIME is False


def test_no_change_when_disabled(adapter: Phase6DecisionAdapter, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 2 (Integration Sim): Verify logic bypasses filtering when flag is False."""
    # Mocking the toggle state in the policy context
    monkeypatch.setattr(p6_config, "ENABLE_PHASE6_RUNTIME", False)
    
    context = create_mock_context(candidates=["L1", "L2"], jammed_links=["L2"])
    original_candidates = ["L1", "L2"]
    
    # Simulate routing policy behavior
    candidates = original_candidates
    if p6_config.ENABLE_PHASE6_RUNTIME:
        candidates = adapter.filter_candidates(context, candidates)
        
    assert candidates == ["L1", "L2"]  # L2 remains because flag is False


def test_deterministic_behavior(adapter: Phase6DecisionAdapter) -> None:
    """Test 3: Same context must yield the exact same filtered output."""
    context = create_mock_context(candidates=["L1", "L2", "L3"], jammed_links=["L1", "L3"])
    
    run_1 = adapter.filter_candidates(context, ["L1", "L2", "L3"])
    run_2 = adapter.filter_candidates(context, ["L1", "L2", "L3"])
    
    assert run_1 == ["L2"]
    assert run_1 == run_2


def test_empty_result_handling(adapter: Phase6DecisionAdapter) -> None:
    """Test 4: If all links are avoided, return an empty list gracefully."""
    # All candidates are jammed
    context = create_mock_context(candidates=["L1", "L2"], jammed_links=["L1", "L2"])
    
    filtered = adapter.filter_candidates(context, ["L1", "L2"])
    
    assert filtered == []  # Should not crash, just returns empty


def test_empty_input_candidates(adapter: Phase6DecisionAdapter) -> None:
    """Test Edge Case: Passing an empty list of candidates."""
    context = create_mock_context(candidates=[], jammed_links=[])
    
    filtered = adapter.filter_candidates(context, [])
    
    assert filtered == []


def test_only_filters_within_candidate_scope(adapter):
    context = create_mock_context(
        candidates=["L1", "L2", "L3"],
        jammed_links=["L2"],
    )

    # routing layer只傳 subset
    filtered = adapter.filter_candidates(context, ["L2"])

    # 必須只影響 L2
    assert filtered == []

# --- Wave-90 Tests (Priority) ---

def test_prioritize_ordering(adapter: Phase6DecisionAdapter) -> None:
    """Test 1: Preferred links are hoisted above allowed links."""
    # L1 is clean (preferred), L2 is degraded (allowed)
    context = create_mock_context(candidates=["L1", "L2"], degraded_links=["L2"])
    
    # Input has L2 before L1
    prioritized = adapter.prioritize_candidates(context, ["L2", "L1"])
    
    # Output must group Preferred (L1) then Allowed (L2)
    assert prioritized == ["L1", "L2"]


def test_stable_ordering(adapter: Phase6DecisionAdapter) -> None:
    """Test 2: Order is preserved within the same priority group."""
    # L1 and L3 are both clean (preferred)
    context = create_mock_context(candidates=["L1", "L3"])
    
    prioritized_1 = adapter.prioritize_candidates(context, ["L1", "L3"])
    prioritized_2 = adapter.prioritize_candidates(context, ["L3", "L1"])
    
    assert prioritized_1 == ["L1", "L3"]
    assert prioritized_2 == ["L3", "L1"]


def test_no_preferred(adapter: Phase6DecisionAdapter) -> None:
    """Test 3: If all candidates are allowed, original order is strictly unchanged."""
    # Both L1 and L2 are degraded (allowed)
    context = create_mock_context(candidates=["L1", "L2"], degraded_links=["L1", "L2"])
    
    prioritized = adapter.prioritize_candidates(context, ["L2", "L1"])
    
    assert prioritized == ["L2", "L1"]


def test_prioritize_deterministic(adapter: Phase6DecisionAdapter) -> None:
    """Test 4: Same input consistently yields the same prioritized output."""
    context = create_mock_context(candidates=["L1", "L2", "L3"], degraded_links=["L2"])
    
    run_1 = adapter.prioritize_candidates(context, ["L3", "L2", "L1"])
    run_2 = adapter.prioritize_candidates(context, ["L3", "L2", "L1"])
    
    # L3, L1 are preferred. L2 is allowed. L3 came before L1 in input.
    assert run_1 == ["L3", "L1", "L2"]
    assert run_1 == run_2

def test_apply_decision_combined(adapter: Phase6DecisionAdapter):
    context = create_mock_context(
        candidates=["L1", "L2", "L3"],
        jammed_links=["L2"],
        degraded_links=["L3"],
    )

    result = adapter.apply_decision(context, ["L3", "L2", "L1"])

    # L2 removed
    # L1 preferred
    # L3 allowed
    assert result == ["L1", "L3"]