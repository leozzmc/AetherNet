import pytest

from router.bundle import Bundle, BundleStatus
from protocol.bundle import BundleProtocolV1


def test_protocol_v1_roundtrip_serialization():
    original = Bundle(
        id="proto-test-1",
        type="telemetry",
        source="lunar-node",
        destination="ground-station",
        priority=100,
        created_at=10,
        ttl_sec=3600,
        size_bytes=250,
        payload_ref="payloads/telemetry/test.json",
        status=BundleStatus.FORWARDING,
        next_hop="leo-relay"
    )

    # 1. Test to_dict
    data = BundleProtocolV1.to_dict(original)
    assert isinstance(data, dict)
    assert data["id"] == "proto-test-1"
    assert data["status"] == "forwarding"
    assert data["next_hop"] == "leo-relay"

    # 2. Test from_dict
    restored = BundleProtocolV1.from_dict(data)
    assert isinstance(restored, Bundle)
    assert restored.id == original.id
    assert restored.status == BundleStatus.FORWARDING
    assert restored.next_hop == "leo-relay"
    assert restored.size_bytes == 250
    assert restored.type == "telemetry"

def test_size_bytes_not_double_count():
    bundle = Bundle(
        id="size-check",
        type="science",
        source="moon",
        destination="earth",
        priority=10,
        created_at=0,
        ttl_sec=100,
        size_bytes=1000,
        payload_ref="data.bin"
    )

    size = BundleProtocolV1.size_bytes(bundle)

    assert size > 1000
    assert size < 2000

def test_protocol_v1_size_bytes_estimation():
    bundle = Bundle(
        id="size-test",
        type="science",
        source="lunar-node",
        destination="ground-station",
        priority=50,
        created_at=0,
        ttl_sec=60,
        size_bytes=5000, # Explicit payload size
        payload_ref="payloads/science/large.json"
    )

    total_size = BundleProtocolV1.size_bytes(bundle)
    
    # Total transport size must be greater than the payload size alone
    # (Payload size + serialized JSON metadata overhead)
    assert total_size > 5000
    
    # Ensure determinism (calling it twice yields the exact same byte count)
    assert total_size == BundleProtocolV1.size_bytes(bundle)