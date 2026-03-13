from sim.reporting import compare_reports

def test_comparison_aggregates_timing_correctly():
    report_a = {
        "scenario_name": "A",
        "bundle_timelines": { "b1": {"delivered_tick": 10}, "b2": {"delivered_tick": 20, "stored_tick": 5} }
    }
    report_b = {
        "scenario_name": "B",
        "bundle_timelines": { "b3": {"delivered_tick": 30}, "b4": {"purged_tick": 5} }
    }
    report_c = {
        "scenario_name": "C",
        "bundle_timelines": {} # No deliveries or purges
    }
    
    comparison = compare_reports([report_a, report_b, report_c])
    agg = comparison["aggregate"]
    
    assert agg["fastest_delivery_tick"] == 10
    assert agg["slowest_delivery_tick"] == 30
    assert "A" in agg["scenarios_with_relay_storage"]
    assert "B" not in agg["scenarios_with_relay_storage"]
    assert "B" in agg["scenarios_with_purge_events"]