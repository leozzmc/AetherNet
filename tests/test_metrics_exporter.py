from metrics.exporter import MetricsCollector

def test_metrics_collection_and_snapshot():
    collector = MetricsCollector()
    
    collector.record_forwarded("telemetry")
    collector.record_forwarded("telemetry")
    collector.record_forwarded("science")
    
    collector.record_stored("telemetry")
    collector.record_delivered("telemetry")
    
    collector.set_queue_depth("queue_depth_lunar", 5)
    
    snapshot = collector.snapshot()
    
    assert snapshot["bundles_forwarded_total"]["telemetry"] == 2
    assert snapshot["bundles_forwarded_total"]["science"] == 1
    assert snapshot["bundles_stored_total"]["telemetry"] == 1
    assert snapshot["bundles_delivered_total"]["telemetry"] == 1
    assert snapshot["queue_depths"]["queue_depth_lunar"] == 5