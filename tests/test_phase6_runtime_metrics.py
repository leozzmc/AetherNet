import pytest

from aether_phase6_runtime.metrics import RoutingMetricsCollector


@pytest.fixture
def collector() -> RoutingMetricsCollector:
    return RoutingMetricsCollector()


def test_metrics_computed_correctly(collector: RoutingMetricsCollector) -> None:
    """Test 1: Verify raw metric values for a single routing decision."""
    original = ["L1", "L2", "L3", "L4"]
    final = ["L1", "L3"]  # L2 and L4 were filtered out
    chosen = "L1"
    decision_map = {"L1": "preferred", "L2": "avoid", "L3": "allowed", "L4": "avoid"}

    collector.record(original, final, chosen, decision_map)
    records = collector.get_records()
    
    assert len(records) == 1
    metric = records[0]
    
    assert metric.total_candidates == 4
    assert metric.filtered_candidates == 2
    assert metric.chosen_link == "L1"
    assert metric.chosen_decision_type == "preferred"


def test_summary_ratios_are_correct(collector: RoutingMetricsCollector) -> None:
    """Test 2: Verify aggregation math across multiple routing decisions."""
    # Run 1: Chose a preferred link. 1 link filtered.
    collector.record(["L1", "L2"], ["L1"], "L1", {"L1": "preferred", "L2": "avoid"})
    
    # Run 2: Chose an allowed link. 0 links filtered.
    collector.record(["L3", "L4"], ["L3", "L4"], "L4", {"L3": "preferred", "L4": "allowed"})
    
    # Run 3: No link chosen (e.g., all were avoid, or queue is full). 2 links filtered.
    collector.record(["L5", "L6"], [], None, {"L5": "avoid", "L6": "avoid"})
    
    summary = collector.summary()
    
    assert summary.total_decisions == 3
    # 1 preferred out of 3 decisions
    assert summary.preferred_ratio == pytest.approx(1 / 3)
    # 1 allowed out of 3 decisions
    assert summary.allowed_ratio == pytest.approx(1 / 3)
    # Total filtered = 1 + 0 + 2 = 3. Average filtered = 3 / 3 = 1.0
    assert summary.average_filtered == 1.0


def test_empty_result_handling(collector: RoutingMetricsCollector) -> None:
    """Test 3: Verify zero-division safety when no decisions have been made."""
    summary = collector.summary()
    
    assert summary.total_decisions == 0
    assert summary.preferred_ratio == 0.0
    assert summary.allowed_ratio == 0.0
    assert summary.average_filtered == 0.0


def test_deterministic_output(collector: RoutingMetricsCollector) -> None:
    """Test 4: Verify same inputs yield byte-identical summaries."""
    collector_a = RoutingMetricsCollector()
    collector_b = RoutingMetricsCollector()
    
    orig, final, chosen, d_map = ["L1"], ["L1"], "L1", {"L1": "preferred"}
    
    collector_a.record(orig, final, chosen, d_map)
    collector_b.record(orig, final, chosen, d_map)
    
    assert collector_a.summary() == collector_b.summary()