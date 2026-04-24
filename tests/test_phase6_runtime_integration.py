from unittest.mock import patch

import pytest

from aether_routing_context import NetworkObservation, RoutingContext
from router.bundle import Bundle
from router.route_scoring import RouteCandidate
from router.routing_policies import ScoredContactAwareRoutingPolicy


class MockContactManager:
    def is_forwarding_allowed(
        self,
        source: str,
        destination: str,
        current_time: int,
    ) -> bool:
        return True


def create_bundle(destination: str) -> Bundle:
    return Bundle(
        id="b1",
        type="telemetry",
        source="N1",
        destination=destination,
        priority=1,
        created_at=0,
        ttl_sec=100,
        size_bytes=100,
        payload_ref="payload-b1",
        next_hop=None,
    )

@pytest.fixture
def candidate_routes():
    return {
        "N1": {
            "N3": [
                RouteCandidate(next_hop="L1", score=10.0),
                RouteCandidate(next_hop="L2", score=90.0),
            ]
        }
    }


def build_test_context(
    jammed_links: list[str] | None = None,
    degraded_links: list[str] | None = None,
) -> RoutingContext:
    if jammed_links is None:
        jammed_links = []
    if degraded_links is None:
        degraded_links = []

    observation = NetworkObservation(
        time_index=0,
        node_ids=["N1", "N3", "L1", "L2"],
        link_ids=["L1", "L2"],
        degraded_links=degraded_links,
        extra_delay_ms_by_link={},
        jammed_links=jammed_links,
        malicious_drop_links=[],
        compromised_nodes=[],
        injected_delay_ms_by_link={},
    )

    return RoutingContext(
        scenario_name="phase6_runtime_integration_test",
        master_seed=42,
        time_index=0,
        source_node_id="N1",
        destination_node_id="N3",
        candidate_link_ids=["L1", "L2"],
        network_observation=observation,
        metadata={},
    )


def test_legacy_mode_remains_unchanged(candidate_routes) -> None:
    policy = ScoredContactAwareRoutingPolicy(
        candidate_routes=candidate_routes,
        contact_manager=MockContactManager(),
        routing_mode="legacy",
    )

    decision = policy.evaluate_decision(
        current_node="N1",
        bundle=create_bundle("N3"),
        current_time=0,
    )

    assert decision.next_hop == "L2"
    assert decision.reason == "selected_scored_candidate"


def test_unknown_routing_mode_raises(candidate_routes) -> None:
    with pytest.raises(ValueError, match="Unsupported routing_mode"):
        ScoredContactAwareRoutingPolicy(
            candidate_routes=candidate_routes,
            contact_manager=MockContactManager(),
            routing_mode="invalid_mode",
        )


@patch.object(ScoredContactAwareRoutingPolicy, "_build_minimal_context")
def test_phase6_balanced_mode_filters_avoid(
    mock_context_builder,
    candidate_routes,
) -> None:
    mock_context_builder.return_value = build_test_context(jammed_links=["L2"])

    policy = ScoredContactAwareRoutingPolicy(
        candidate_routes=candidate_routes,
        contact_manager=MockContactManager(),
        routing_mode="phase6_balanced",
    )

    decision = policy.evaluate_decision(
        current_node="N1",
        bundle=create_bundle("N3"),
        current_time=0,
    )

    assert decision.next_hop == "L1"
    assert decision.reason == "selected_scored_candidate"


@patch.object(ScoredContactAwareRoutingPolicy, "_build_minimal_context")
def test_phase6_adaptive_mode_is_deterministic(
    mock_context_builder,
    candidate_routes,
) -> None:
    mock_context_builder.return_value = build_test_context(degraded_links=["L2"])

    policy = ScoredContactAwareRoutingPolicy(
        candidate_routes=candidate_routes,
        contact_manager=MockContactManager(),
        routing_mode="phase6_adaptive",
    )

    decision_a = policy.evaluate_decision(
        current_node="N1",
        bundle=create_bundle("N3"),
        current_time=0,
    )
    decision_b = policy.evaluate_decision(
        current_node="N1",
        bundle=create_bundle("N3"),
        current_time=0,
    )

    assert decision_a == decision_b


@patch.object(ScoredContactAwareRoutingPolicy, "_build_minimal_context")
def test_phase6_filters_all_candidates_safely(
    mock_context_builder,
    candidate_routes,
) -> None:
    mock_context_builder.return_value = build_test_context(jammed_links=["L1", "L2"])

    policy = ScoredContactAwareRoutingPolicy(
        candidate_routes=candidate_routes,
        contact_manager=MockContactManager(),
        routing_mode="phase6_balanced",
    )

    decision = policy.evaluate_decision(
        current_node="N1",
        bundle=create_bundle("N3"),
        current_time=0,
    )

    assert decision.next_hop is None
    assert decision.reason == "phase6_filtered_all"


def test_phase6_minimal_context_is_deterministic(candidate_routes) -> None:
    policy = ScoredContactAwareRoutingPolicy(
        candidate_routes=candidate_routes,
        contact_manager=MockContactManager(),
        routing_mode="phase6_balanced",
    )

    context_a = policy._build_minimal_context(
        current_node="N1",
        destination="N3",
        current_time=7,
        candidate_link_ids=["L2", "L1"],
    )
    context_b = policy._build_minimal_context(
        current_node="N1",
        destination="N3",
        current_time=7,
        candidate_link_ids=["L2", "L1"],
    )

    assert context_a.to_dict() == context_b.to_dict()