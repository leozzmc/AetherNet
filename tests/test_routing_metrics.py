import pytest
from metrics.routing_metrics import RoutingMetricsCollector
from router.routing_decision import RoutingDecision


def test_routing_metrics_collector_accumulates_deterministically():
    collector = RoutingMetricsCollector(policy_name="test_policy")
    
    collector.record(RoutingDecision(next_hop="relay-1", reason="selected_static_route"))
    collector.record(RoutingDecision(next_hop="relay-1", reason="selected_static_route"))
    collector.record(RoutingDecision(next_hop="relay-2", reason="selected_scored_candidate"))
    collector.record(RoutingDecision(next_hop=None, reason="contact_blocked"))
    collector.record(RoutingDecision(next_hop=None, reason="at_destination"))
    
    snap = collector.snapshot()
    
    assert snap["policy_name"] == "test_policy"
    assert snap["total_lookups"] == 5
    
    assert snap["reason_counts"]["selected_static_route"] == 2
    assert snap["reason_counts"]["selected_scored_candidate"] == 1
    assert snap["reason_counts"]["contact_blocked"] == 1
    assert snap["reason_counts"]["at_destination"] == 1
    assert snap["reason_counts"]["no_route"] == 0 # Defaults to 0 correctly
    
    assert snap["next_hop_counts"]["relay-1"] == 2
    assert snap["next_hop_counts"]["relay-2"] == 1
    assert snap["next_hop_counts"]["None"] == 2