from router.bundle import Bundle, BundleStatus
from bundle_queue.priority_queue import StrictPriorityQueue


def test_bundle_is_expired_boundary():
    b = Bundle(
        id="1",
        type="telemetry",
        source="moon",
        destination="earth",
        priority=100,
        created_at=10,
        ttl_sec=30,
        size_bytes=100,
        payload_ref="payloads/telemetry/test.json",
    )

    assert b.is_expired(current_time=39) is False
    assert b.is_expired(current_time=40) is True


def test_queue_drops_expired_bundles():
    pq = StrictPriorityQueue()
    b = Bundle(
        id="1",
        type="telemetry",
        source="moon",
        destination="earth",
        priority=100,
        created_at=0,
        ttl_sec=10,
        size_bytes=100,
        payload_ref="payloads/telemetry/test.json",
    )

    pq.enqueue(b)
    out = pq.dequeue(current_time=10)

    assert out is None
    assert b.status == BundleStatus.EXPIRED
    assert pq.size() == 0


def test_to_dict_serializes_status_as_string():
    b = Bundle(
        id="1",
        type="telemetry",
        source="moon",
        destination="earth",
        priority=100,
        created_at=0,
        ttl_sec=10,
        size_bytes=100,
        payload_ref="payloads/telemetry/test.json",
    )
    data = b.to_dict()
    assert data["status"] == "queued"