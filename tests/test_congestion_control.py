from router.bundle import Bundle
from bundle_queue.priority_queue import StrictPriorityQueue
from metrics.exporter import MetricsCollector


def create_bundle(b_id: str, b_type: str, prio: int) -> Bundle:
    return Bundle(
        id=b_id,
        type=b_type,
        source="A",
        destination="B",
        priority=prio,
        created_at=0,
        ttl_sec=100,
        size_bytes=100,
        payload_ref="ref",
    )


def test_unlimited_queue_remains_unchanged():
    q = StrictPriorityQueue()  # max_size=None

    for i in range(10):
        b = create_bundle(f"sci-{i}", "science", 50)
        assert q.enqueue(b) is True

    assert q.size() == 10


def test_full_queue_rejects_incoming_low_priority():
    metrics = MetricsCollector()
    q = StrictPriorityQueue(max_size=2, metrics=metrics)

    q.enqueue(create_bundle("tel-1", "telemetry", 100))
    q.enqueue(create_bundle("tel-2", "telemetry", 100))

    sci_bundle = create_bundle("sci-1", "science", 50)
    assert q.enqueue(sci_bundle) is False

    assert q.size() == 2
    assert metrics.bundles_dropped_total["science"] == 1
    assert "sci-1" in metrics.dropped_bundle_ids


def test_full_queue_evicts_lowest_priority_for_high_priority():
    metrics = MetricsCollector()
    q = StrictPriorityQueue(max_size=2, metrics=metrics)

    q.enqueue(create_bundle("sci-1", "science", 50))
    q.enqueue(create_bundle("sci-2", "science", 50))

    tel_bundle = create_bundle("tel-1", "telemetry", 100)
    assert q.enqueue(tel_bundle) is True

    assert q.size() == 2

    b1 = q.dequeue(0)
    b2 = q.dequeue(0)

    assert b1.id == "tel-1"
    assert b2.id == "sci-2"

    assert metrics.bundles_dropped_total["science"] == 1
    assert "sci-1" in metrics.dropped_bundle_ids


def test_equal_priority_rejects_incoming():
    metrics = MetricsCollector()
    q = StrictPriorityQueue(max_size=2, metrics=metrics)

    q.enqueue(create_bundle("tel-1", "telemetry", 100))
    q.enqueue(create_bundle("tel-2", "telemetry", 100))

    tel_3 = create_bundle("tel-3", "telemetry", 100)
    assert q.enqueue(tel_3) is False

    assert q.size() == 2
    assert metrics.bundles_dropped_total["telemetry"] == 1
    assert "tel-3" in metrics.dropped_bundle_ids