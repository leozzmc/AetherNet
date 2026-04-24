from aether_phase6_runtime.simulation_metrics import (
    SimulationRoutingMetric,
    SimulationRoutingMetricsCollector,
    SimulationRoutingMetricsSummary,
)


def test_single_metric_to_dict() -> None:
    metric = SimulationRoutingMetric(
        routing_mode="phase6_balanced",
        selected_next_hop="L2",
        decision_reason="selected_scored_candidate",
        candidate_count_before=4,
        candidate_count_after=2,
        phase6_filtered_all=False,
    )

    data = metric.to_dict()

    assert data["type"] == "simulation_routing_metric"
    assert data["version"] == "1.0"
    assert data["routing_mode"] == "phase6_balanced"
    assert data["selected_next_hop"] == "L2"
    assert data["decision_reason"] == "selected_scored_candidate"
    assert data["candidate_count_before"] == 4
    assert data["candidate_count_after"] == 2
    assert data["phase6_filtered_all"] is False


def test_collector_records_metrics() -> None:
    collector = SimulationRoutingMetricsCollector()

    collector.record_policy_decision(
        routing_mode="legacy",
        selected_next_hop="L1",
        decision_reason="selected_scored_candidate",
        candidate_count_before=3,
        candidate_count_after=3,
    )

    records = collector.get_records()

    assert len(records) == 1
    assert records[0].routing_mode == "legacy"
    assert records[0].phase6_filtered_all is False


def test_summary_counts_routing_modes_and_hops() -> None:
    collector = SimulationRoutingMetricsCollector()

    collector.record_policy_decision("legacy", "L1", "reason", 2, 2)
    collector.record_policy_decision("phase6_balanced", "L2", "reason", 2, 1)
    collector.record_policy_decision(
        "phase6_balanced",
        None,
        "phase6_filtered_all",
        2,
        0,
    )

    summary = collector.summary()

    assert summary.total_decisions == 3
    assert summary.mode_counts["legacy"] == 1
    assert summary.mode_counts["phase6_balanced"] == 2
    assert summary.filtered_all_count == 1
    assert summary.selected_next_hop_counts["L1"] == 1
    assert summary.selected_next_hop_counts["L2"] == 1
    assert summary.selected_next_hop_counts["NONE"] == 1


def test_summary_to_dict_schema_is_stable() -> None:
    summary = SimulationRoutingMetricsSummary(
        total_decisions=2,
        mode_counts={"phase6_balanced": 1, "legacy": 1},
        filtered_all_count=0,
        selected_next_hop_counts={"Z_NODE": 1, "A_NODE": 1},
    )

    data = summary.to_dict()

    assert data["type"] == "simulation_routing_metrics_summary"
    assert data["version"] == "1.0"
    assert data["total_decisions"] == 2


def test_deterministic_summary_ordering() -> None:
    summary = SimulationRoutingMetricsSummary(
        total_decisions=3,
        mode_counts={
            "phase6_balanced": 1,
            "legacy": 1,
            "phase6_adaptive": 1,
        },
        filtered_all_count=0,
        selected_next_hop_counts={"Z_NODE": 1, "A_NODE": 1},
    )

    data = summary.to_dict()

    assert list(data["mode_counts"].keys()) == [
        "legacy",
        "phase6_adaptive",
        "phase6_balanced",
    ]
    assert list(data["selected_next_hop_counts"].keys()) == [
        "A_NODE",
        "Z_NODE",
    ]


def test_mutation_safety() -> None:
    summary = SimulationRoutingMetricsSummary(
        total_decisions=1,
        mode_counts={"legacy": 1},
        filtered_all_count=0,
        selected_next_hop_counts={"L1": 1},
    )

    data = summary.to_dict()
    data["mode_counts"]["HACKED"] = 999

    assert "HACKED" not in summary.mode_counts

    original_mode_counts = {"legacy": 1}
    summary_b = SimulationRoutingMetricsSummary(
        total_decisions=1,
        mode_counts=original_mode_counts,
        filtered_all_count=0,
        selected_next_hop_counts={},
    )
    original_mode_counts["HACKED"] = 999

    assert "HACKED" not in summary_b.mode_counts


def test_empty_summary_handling() -> None:
    collector = SimulationRoutingMetricsCollector()

    summary = collector.summary()

    assert summary.total_decisions == 0
    assert summary.mode_counts == {}
    assert summary.filtered_all_count == 0
    assert summary.selected_next_hop_counts == {}