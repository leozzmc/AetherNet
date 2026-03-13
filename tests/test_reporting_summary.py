import json

from sim.reporting import summarize_report


def test_summarize_report_keys_and_values():
    mock_report = {
        "scenario_name": "test_scenario",
        "simulation_end_time": 100,
        "final_metrics": {
            "bundles_forwarded_total": {"telemetry": 2, "science": 1},
            "bundles_stored_total": {"telemetry": 1},
            "bundles_delivered_total": {"telemetry": 1, "science": 1},
            "bundles_expired_total": {"telemetry": 1},
        },
        "store_bundle_ids_remaining": ["b1", "b2"],
        "purged_bundle_ids": ["b3"],
        "delivered_bundle_ids": ["b4", "b5"],
    }

    summary = summarize_report(mock_report)

    assert summary["scenario_name"] == "test_scenario"
    assert summary["forwarded_total"] == 3
    assert summary["stored_total"] == 1
    assert summary["delivered_total"] == 2
    assert summary["expired_total"] == 1
    assert summary["remaining_store_count"] == 2
    assert summary["purged_count"] == 1
    assert summary["delivered_bundle_count"] == 2

    json.dumps(summary)