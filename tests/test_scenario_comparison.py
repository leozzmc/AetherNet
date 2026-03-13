from sim.reporting import compare_reports


def test_compare_reports_aggregation():
    report1 = {
        "scenario_name": "run1",
        "final_metrics": {"bundles_expired_total": {"tel": 1}},
        "delivered_bundle_ids": ["a1", "a2"],
        "purged_bundle_ids": ["a3"],
    }
    report2 = {
        "scenario_name": "run2",
        "final_metrics": {"bundles_expired_total": {"tel": 2}},
        "delivered_bundle_ids": ["b1"],
        "purged_bundle_ids": ["b2", "b3"],
    }

    comparison = compare_reports([report1, report2])

    assert comparison["scenario_names"] == ["run1", "run2"]
    assert len(comparison["per_scenario_summaries"]) == 2

    agg = comparison["aggregate"]
    assert agg["total_delivered_bundles"] == 3
    assert agg["total_expired_bundles"] == 3
    assert agg["total_purged_bundles"] == 3