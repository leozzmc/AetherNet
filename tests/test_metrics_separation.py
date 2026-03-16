import pytest

from metrics.exporter import MetricsCollector
from router.bundle import Bundle, BundleStatus


@pytest.fixture
def standard_bundle() -> Bundle:
    return Bundle(
        id="tel-001",
        type="telemetry",
        source="lunar-node",
        destination="ground-station",
        priority=100,
        created_at=5,
        ttl_sec=3600,
        size_bytes=5000,
        payload_ref="sensor_data.bin",
        status=BundleStatus.QUEUED,
    )


@pytest.fixture
def fragment_bundle() -> Bundle:
    return Bundle(
        id="tel-001.frag-0",
        type="telemetry",
        source="lunar-node",
        destination="ground-station",
        priority=100,
        created_at=5,
        ttl_sec=3600,
        size_bytes=1000,
        payload_ref="sensor_data.bin.frag-0",
        is_fragment=True,
        original_bundle_id="tel-001",
        fragment_index=0,
        total_fragments=5,
        status=BundleStatus.QUEUED,
    )


def test_legacy_string_updates_bundle_counters_only():
    collector = MetricsCollector()

    collector.record_delivered("science")
    collector.record_forwarded("science")
    collector.record_stored("science")
    collector.record_expired("science", bundle_id="sci-001")
    collector.record_dropped("science", bundle_id="sci-002")

    assert collector.bundles_delivered_total["science"] == 1
    assert collector.bundles_forwarded_total["science"] == 1
    assert collector.bundles_stored_total["science"] == 1
    assert collector.bundles_expired_total["science"] == 1
    assert collector.bundles_dropped_total["science"] == 1

    assert "science" not in collector.fragments_delivered_total
    assert "science" not in collector.fragments_forwarded_total
    assert "science" not in collector.fragments_stored_total
    assert "science" not in collector.fragments_expired_total
    assert "science" not in collector.fragments_dropped_total


def test_non_fragment_bundle_updates_bundle_counters_only(standard_bundle):
    collector = MetricsCollector()

    collector.record_delivered(standard_bundle)
    collector.record_forwarded(standard_bundle)
    collector.record_stored(standard_bundle)
    collector.record_expired(standard_bundle)
    collector.record_dropped(standard_bundle, bundle_id=standard_bundle.id)

    assert collector.bundles_delivered_total["telemetry"] == 1
    assert collector.bundles_forwarded_total["telemetry"] == 1
    assert collector.bundles_stored_total["telemetry"] == 1
    assert collector.bundles_expired_total["telemetry"] == 1
    assert collector.bundles_dropped_total["telemetry"] == 1

    assert "telemetry" not in collector.fragments_delivered_total
    assert "telemetry" not in collector.fragments_forwarded_total
    assert "telemetry" not in collector.fragments_stored_total
    assert "telemetry" not in collector.fragments_expired_total
    assert "telemetry" not in collector.fragments_dropped_total


def test_fragment_bundle_updates_fragment_counters_only(fragment_bundle):
    collector = MetricsCollector()

    collector.record_delivered(fragment_bundle)
    collector.record_forwarded(fragment_bundle)
    collector.record_stored(fragment_bundle)
    collector.record_expired(fragment_bundle)
    collector.record_dropped(fragment_bundle, bundle_id=fragment_bundle.id)

    assert collector.fragments_delivered_total["telemetry"] == 1
    assert collector.fragments_forwarded_total["telemetry"] == 1
    assert collector.fragments_stored_total["telemetry"] == 1
    assert collector.fragments_expired_total["telemetry"] == 1
    assert collector.fragments_dropped_total["telemetry"] == 1

    assert "telemetry" not in collector.bundles_delivered_total
    assert "telemetry" not in collector.bundles_forwarded_total
    assert "telemetry" not in collector.bundles_stored_total
    assert "telemetry" not in collector.bundles_expired_total
    assert "telemetry" not in collector.bundles_dropped_total


def test_record_expired_bundle_object_uses_bundle_id_for_purge_tracking(standard_bundle):
    collector = MetricsCollector()

    collector.record_expired(standard_bundle)

    assert standard_bundle.id in collector.purged_bundle_ids
    assert standard_bundle.id in collector.recent_purged_ids


def test_snapshot_includes_bundle_and_fragment_counters(standard_bundle, fragment_bundle):
    collector = MetricsCollector()

    collector.record_delivered(standard_bundle)
    collector.record_delivered(fragment_bundle)

    snapshot = collector.snapshot()

    assert snapshot["bundles_delivered_total"]["telemetry"] == 1
    assert snapshot["fragments_delivered_total"]["telemetry"] == 1

    assert "bundles_forwarded_total" in snapshot
    assert "fragments_forwarded_total" in snapshot
    assert "bundles_stored_total" in snapshot
    assert "fragments_stored_total" in snapshot
    assert "bundles_expired_total" in snapshot
    assert "fragments_expired_total" in snapshot
    assert "bundles_dropped_total" in snapshot
    assert "fragments_dropped_total" in snapshot


def test_queue_depth_behavior_remains_unchanged():
    collector = MetricsCollector()

    collector.set_queue_depth("lunar_queue", 3)

    assert collector.queue_depths["lunar_queue"] == 3
    assert collector.last_queue_depths["lunar_queue"] == 3