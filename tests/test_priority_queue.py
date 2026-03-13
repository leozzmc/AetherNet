from bundle_queue.priority_queue import StrictPriorityQueue
from bundle_queue.classifiers import classify_bundle
from router.bundle import Bundle, BundleStatus


def test_strict_priority_ordering():
    pq = StrictPriorityQueue()

    b_science = Bundle(
        id="1",
        type="science",
        source="moon",
        destination="earth",
        priority=classify_bundle("science"),
        created_at=0,
        ttl_sec=60,
        size_bytes=1000,
        payload_ref="payloads/science/test.json",
    )
    b_telemetry = Bundle(
        id="2",
        type="telemetry",
        source="moon",
        destination="earth",
        priority=classify_bundle("telemetry"),
        created_at=0,
        ttl_sec=60,
        size_bytes=100,
        payload_ref="payloads/telemetry/test.json",
    )

    pq.enqueue(b_science)
    pq.enqueue(b_telemetry)

    first_out = pq.dequeue(current_time=1)
    assert first_out is not None
    assert first_out.type == "telemetry"

    second_out = pq.dequeue(current_time=1)
    assert second_out is not None
    assert second_out.type == "science"


def test_fifo_within_same_priority():
    pq = StrictPriorityQueue()
    prio = classify_bundle("telemetry")

    b1 = Bundle(
        id="t1",
        type="telemetry",
        source="moon",
        destination="earth",
        priority=prio,
        created_at=0,
        ttl_sec=60,
        size_bytes=100,
        payload_ref="payloads/telemetry/t1.json",
    )
    b2 = Bundle(
        id="t2",
        type="telemetry",
        source="moon",
        destination="earth",
        priority=prio,
        created_at=1,
        ttl_sec=60,
        size_bytes=100,
        payload_ref="payloads/telemetry/t2.json",
    )

    pq.enqueue(b1)
    pq.enqueue(b2)

    assert pq.dequeue(current_time=2).id == "t1"
    assert pq.dequeue(current_time=2).id == "t2"


def test_expired_high_priority_does_not_block_lower_priority():
    pq = StrictPriorityQueue()

    expired_high = Bundle(
        id="high",
        type="telemetry",
        source="moon",
        destination="earth",
        priority=100,
        created_at=0,
        ttl_sec=5,
        size_bytes=100,
        payload_ref="payloads/telemetry/high.json",
    )
    valid_low = Bundle(
        id="low",
        type="science",
        source="moon",
        destination="earth",
        priority=50,
        created_at=0,
        ttl_sec=60,
        size_bytes=1000,
        payload_ref="payloads/science/low.json",
    )

    pq.enqueue(expired_high)
    pq.enqueue(valid_low)

    out = pq.dequeue(current_time=10)

    assert expired_high.status == BundleStatus.EXPIRED
    assert out is not None
    assert out.id == "low"