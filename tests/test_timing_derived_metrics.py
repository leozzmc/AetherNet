from sim.reporting import summarize_report


def test_derived_timing_fields():
    mock_report = {
        "scenario_name": "timing_test",
        "injected_bundle_count": 3,
        "bundle_timelines": {
            "b1": {"first_forwarded_tick": 2, "stored_tick": 5, "delivered_tick": 10},
            "b2": {"first_forwarded_tick": 3, "stored_tick": 5, "delivered_tick": 15},
            "b3": {"first_forwarded_tick": 4, "purged_tick": 8},
        },
        "delivered_bundle_ids": ["b1", "b2"],
        "purged_bundle_ids": ["b3"],
        "store_bundle_ids_remaining": [],
        "final_metrics": {
            "bundles_delivered_total": {"telemetry": 2},
            "bundles_expired_total": {"telemetry": 1},
            "bundles_stored_total": {"telemetry": 2},
            "bundles_forwarded_total": {"telemetry": 3},
        },
    }

    summary = summarize_report(mock_report)

    assert summary["first_delivery_tick"] == 10
    assert summary["last_delivery_tick"] == 15
    assert summary["delivery_span_ticks"] == 5
    assert summary["average_delivery_tick"] == 12.5
    assert summary["first_purge_tick"] == 8
    assert summary["relay_storage_observed"] is True
    assert summary["delivered_ratio"] == 0.67


def test_timing_fields_handle_missing_data_gracefully():
    mock_empty = {"bundle_timelines": {}}
    summary = summarize_report(mock_empty)

    assert summary["first_delivery_tick"] is None
    assert summary["average_delivery_tick"] is None
    assert summary["relay_storage_observed"] is False