import pytest

from protocol.bundle import BundleProtocolV1
from protocol.fragmentation import (
    compute_contact_capacity_bytes,
    fragment_bundle,
    fragment_bundle_contact_aware,
)
from router.bundle import Bundle, BundleStatus
from router.contact_manager import Contact


@pytest.fixture
def oversized_bundle() -> Bundle:
    return Bundle(
        id="sci-001",
        type="science",
        source="lunar-node",
        destination="ground-station",
        priority=50,
        created_at=10,
        ttl_sec=3600,
        size_bytes=2500,
        payload_ref="data.bin",
    )


# --- Legacy Wave-23 Tests ---


def test_no_fragmentation_needed(oversized_bundle):
    result = fragment_bundle(oversized_bundle, max_fragment_size_bytes=3000)

    assert len(result) == 1
    assert result[0] is oversized_bundle
    assert result[0].is_fragment is False


def test_deterministic_fragmentation(oversized_bundle):
    fragments = fragment_bundle(oversized_bundle, max_fragment_size_bytes=1000)

    assert len(fragments) == 3
    assert fragments[0].size_bytes == 1000
    assert fragments[1].size_bytes == 1000
    assert fragments[2].size_bytes == 500
    assert sum(f.size_bytes for f in fragments) == oversized_bundle.size_bytes

    for i, frag in enumerate(fragments):
        assert frag.is_fragment is True
        assert frag.original_bundle_id == "sci-001"
        assert frag.total_fragments == 3
        assert frag.fragment_index == i
        assert frag.id == f"sci-001.frag-{i}"
        assert frag.payload_ref == f"data.bin.frag-{i}"
        assert frag.type == "science"
        assert frag.priority == 50
        assert frag.destination == "ground-station"


def test_fragment_serialization_roundtrip(oversized_bundle):
    fragments = fragment_bundle(oversized_bundle, max_fragment_size_bytes=1000)
    frag_0 = fragments[0]

    data = BundleProtocolV1.to_dict(frag_0)
    assert data["is_fragment"] is True
    assert data["fragment_index"] == 0

    restored = BundleProtocolV1.from_dict(data)
    assert restored.id == frag_0.id
    assert restored.is_fragment is True
    assert restored.original_bundle_id == "sci-001"
    assert restored.size_bytes == 1000


def test_zero_or_negative_max_size(oversized_bundle):
    with pytest.raises(ValueError, match="strictly positive"):
        fragment_bundle(oversized_bundle, max_fragment_size_bytes=0)

    with pytest.raises(ValueError, match="strictly positive"):
        fragment_bundle(oversized_bundle, max_fragment_size_bytes=-500)


# --- Wave-26: Contact-Aware Fragmentation Tests ---


def test_compute_contact_capacity_bytes():
    # duration = 10s, bw = 8 kbit/s = 1000 bytes/s -> 10,000 bytes total capacity
    contact = Contact(
        source="A",
        target="B",
        start_time=0,
        end_time=10,
        one_way_delay_ms=0,
        bandwidth_kbit=8,
    )

    assert compute_contact_capacity_bytes(contact) == 10000


def test_contact_aware_fragmentation_fits(oversized_bundle):
    # Bundle is 2500 bytes. Contact capacity is 10000 bytes.
    contact = Contact(
        source="lunar-node",
        target="leo-relay",
        start_time=0,
        end_time=10,
        one_way_delay_ms=0,
        bandwidth_kbit=8,
    )

    result = fragment_bundle_contact_aware(oversized_bundle, contact)

    assert len(result) == 1
    assert result[0] is oversized_bundle
    assert result[0].is_fragment is False


def test_contact_aware_fragmentation_exceeds(oversized_bundle):
    # Bundle is 2500 bytes. Contact duration 2s, bw 8 kbit/s -> capacity 2000 bytes.
    contact = Contact(
        source="lunar-node",
        target="leo-relay",
        start_time=0,
        end_time=2,
        one_way_delay_ms=0,
        bandwidth_kbit=8,
    )

    result = fragment_bundle_contact_aware(oversized_bundle, contact)

    assert len(result) == 2
    assert result[0].size_bytes == 2000
    assert result[1].size_bytes == 500
    assert sum(f.size_bytes for f in result) == oversized_bundle.size_bytes


def test_contact_aware_zero_capacity_raises(oversized_bundle):
    # Zero bandwidth
    contact_zero_bw = Contact(
        source="A",
        target="B",
        start_time=0,
        end_time=10,
        one_way_delay_ms=0,
        bandwidth_kbit=0,
    )
    with pytest.raises(ValueError, match="strictly positive"):
        fragment_bundle_contact_aware(oversized_bundle, contact_zero_bw)

    # Zero duration
    contact_zero_dur = Contact(
        source="A",
        target="B",
        start_time=10,
        end_time=10,
        one_way_delay_ms=0,
        bandwidth_kbit=8,
    )
    with pytest.raises(ValueError, match="strictly positive"):
        fragment_bundle_contact_aware(oversized_bundle, contact_zero_dur)


def test_contact_aware_negative_bandwidth_raises(oversized_bundle):
    contact_negative_bw = Contact(
        source="A",
        target="B",
        start_time=0,
        end_time=10,
        one_way_delay_ms=0,
        bandwidth_kbit=-8,
    )

    with pytest.raises(ValueError, match="strictly positive"):
        fragment_bundle_contact_aware(oversized_bundle, contact_negative_bw)