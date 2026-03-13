from sim.reporting import summarize_report

def test_derived_ratios_and_outcomes():
    mock_report = {
        "final_metrics": {
            "bundles_delivered_total": {"tel": 2},
            "bundles_expired_total": {"tel": 1}
        },
        "delivered_bundle_ids": ["b1", "b2"],
        "purged_bundle_ids": ["b3"]
    }
    
    # Test partial delivery with expiry
    summary = summarize_report(mock_report, initial_injected_count=3)
    
    assert summary["delivered_ratio"] == 0.67
    assert summary["expired_ratio"] == 0.33
    assert summary["outcome"] == "expiry_observed"
    
    # Test perfect delivery
    mock_perfect = {
        "delivered_bundle_ids": ["b1", "b2", "b3"],
        "purged_bundle_ids": []
    }
    summary_perf = summarize_report(mock_perfect, initial_injected_count=3)
    assert summary_perf["outcome"] == "successful_delivery"
    assert summary_perf["delivered_ratio"] == 1.0

    # Test zero injection edge case
    summary_zero = summarize_report(mock_perfect, initial_injected_count=0)
    assert summary_zero["delivered_ratio"] == 0.0