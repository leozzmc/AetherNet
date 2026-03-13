import json

from sim.reporting import compare_reports


def test_comparison_contains_enriched_aggregate_fields():
    r1 = {
        "scenario_name": "default_multihop",
        "injected_bundle_count": 3,
        "delivered_bundle_ids": ["a"],
        "store_bundle_ids_remaining": ["b", "c"],
        "purged_bundle_ids": [],
        "final_metrics": {
            "bundles_expired_total": {},
            "bundles_delivered_total": {"telemetry": 1},
            "bundles_stored_total": {},
            "bundles_forwarded_total": {"telemetry": 1},
        },
    }
    r2 = {
        "scenario_name": "expiry_before_contact",
        "injected_bundle_count": 3,
        "delivered_bundle_ids": ["x", "y"],
        "store_bundle_ids_remaining": [],
        "purged_bundle_ids": ["z"],
        "final_metrics": {
            "bundles_expired_total": {"telemetry": 1},
            "bundles_delivered_total": {"telemetry": 2},
            "bundles_stored_total": {},
            "bundles_forwarded_total": {"telemetry": 2},
        },
    }

    comp = compare_reports([r1, r2])

    assert comp["scenario_names"] == ["default_multihop", "expiry_before_contact"]
    assert len(comp["per_scenario_summaries"]) == 2

    agg = comp["aggregate"]
    assert "successful_scenarios" in agg
    assert "scenarios_with_expiry" in agg
    assert agg["max_remaining_store_count"] == 2
    assert agg["max_delivered_bundle_count"] == 2

    for summary in comp["per_scenario_summaries"]:
        assert "outcome" in summary
        assert "delivered_ratio" in summary
        assert "remaining_store_ratio" in summary

    json.dumps(comp)