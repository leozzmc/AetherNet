from sim.reporting import compare_reports, summarize_report


def test_summarize_report_separates_bundle_and_fragment_metrics():
    mock_report = {
        "scenario_name": "test_frag_metrics",
        "final_metrics": {
            "bundles_delivered_total": {"science": 2, "telemetry": 1},
            "bundles_expired_total": {"telemetry": 1},
            "bundles_dropped_total": {"video": 1},
            "fragments_forwarded_total": {"science": 4},
            "fragments_stored_total": {"science": 2},
            "fragments_delivered_total": {"science": 5},
            "fragments_expired_total": {"telemetry": 3},
            "fragments_dropped_total": {"video": 2},
        },
        "delivered_bundle_ids": ["b1", "b2", "b3"],
        "injected_bundle_count": 3,
    }

    summary = summarize_report(mock_report)

    assert summary["delivered_total"] == 3
    assert summary["expired_total"] == 1
    assert summary["dropped_total"] == 1
    assert summary["delivered_bundle_count"] == 3

    assert summary["fragments_forwarded_total"] == 4
    assert summary["fragments_stored_total"] == 2
    assert summary["fragments_delivered_total"] == 5
    assert summary["fragments_expired_total"] == 3
    assert summary["fragments_dropped_total"] == 2


def test_compare_reports_aggregates_fragment_metrics_across_scenarios():
    mock_reports = [
        {
            "scenario_name": "scenario_a",
            "final_metrics": {
                "fragments_forwarded_total": {"science": 3},
                "fragments_stored_total": {"science": 1},
                "fragments_delivered_total": {"science": 3},
                "fragments_expired_total": {"telemetry": 1},
                "fragments_dropped_total": {"video": 2},
            },
            "injected_bundle_count": 5,
        },
        {
            "scenario_name": "scenario_b",
            "final_metrics": {
                "fragments_forwarded_total": {"science": 4},
                "fragments_stored_total": {"science": 2},
                "fragments_delivered_total": {"science": 4},
                "fragments_expired_total": {"telemetry": 2},
                "fragments_dropped_total": {"video": 1},
            },
            "injected_bundle_count": 5,
        },
    ]

    comparison = compare_reports(mock_reports)
    aggregate = comparison["aggregate"]

    assert aggregate["total_forwarded_fragments"] == 7
    assert aggregate["total_stored_fragments"] == 3
    assert aggregate["total_delivered_fragments"] == 7
    assert aggregate["total_expired_fragments"] == 3
    assert aggregate["total_dropped_fragments"] == 3