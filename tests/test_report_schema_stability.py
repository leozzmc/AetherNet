import json
from sim.reporting import summarize_report, compare_reports

def test_final_report_schema_keys():
    # Mocking the simulator's build_final_report output
    mock_report = {
        "scenario_name": "test",
        "simulation_start_time": 0,
        "simulation_end_time": 10,
        "tick_size": 1,
        "final_metrics": {
            "bundles_forwarded_total": {"tel": 1},
            "bundles_delivered_total": {},
            "bundles_stored_total": {},
            "bundles_expired_total": {},
            "purged_bundle_ids": [],
            "last_queue_depths": {}
        },
        "store_bundle_ids_remaining": ["b1"],
        "delivered_bundle_ids": [],
        "purged_bundle_ids": [],
        "notes": []
    }
    
    # 1. Test Summary Extraction
    summary = summarize_report(mock_report)
    assert "scenario_name" in summary
    assert "simulation_end_time" in summary
    assert "forwarded_total" in summary
    assert "stored_total" in summary
    assert "delivered_total" in summary
    assert "expired_total" in summary
    assert "remaining_store_count" in summary
    assert "purged_count" in summary
    assert "delivered_bundle_count" in summary
    
    # 2. Test Comparison Aggregation
    comparison = compare_reports([mock_report, mock_report])
    assert "scenario_names" in comparison
    assert "per_scenario_summaries" in comparison
    assert "aggregate" in comparison
    
    agg = comparison["aggregate"]
    assert "total_delivered_bundles" in agg
    assert "total_expired_bundles" in agg
    assert "total_purged_bundles" in agg
    
    # Ensure JSON serializable
    assert json.dumps(comparison)