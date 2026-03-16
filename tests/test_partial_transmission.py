import pytest

from protocol.partial_transmission import split_bundle_for_partial_transmission
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
        next_hop="leo-relay",
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
    )


def test_capacity_zero_or_negative_raises(standard_bundle):
    with pytest.raises(ValueError, match="strictly positive"):
        split_bundle_for_partial_transmission(standard_bundle, capacity_bytes=0)

    with pytest.raises(ValueError, match="strictly positive"):
        split_bundle_for_partial_transmission(standard_bundle, capacity_bytes=-500)


def test_already_fragmented_raises(fragment_bundle):
    with pytest.raises(ValueError, match="not yet supported"):
        split_bundle_for_partial_transmission(fragment_bundle, capacity_bytes=500)


def test_bundle_fits_entirely(standard_bundle):
    transmitted, residual = split_bundle_for_partial_transmission(standard_bundle, capacity_bytes=5000)
    assert transmitted is standard_bundle
    assert residual is None

    transmitted, residual = split_bundle_for_partial_transmission(standard_bundle, capacity_bytes=10000)
    assert transmitted is standard_bundle
    assert residual is None


def test_partial_split_returns_two_fragments_with_correct_sizes(standard_bundle):
    capacity = 2000
    transmitted, residual = split_bundle_for_partial_transmission(standard_bundle, capacity_bytes=capacity)

    assert transmitted is not None
    assert residual is not None
    assert transmitted.size_bytes == capacity
    assert residual.size_bytes == standard_bundle.size_bytes - capacity
    assert transmitted.size_bytes + residual.size_bytes == standard_bundle.size_bytes


def test_partial_split_metadata_preservation_and_fragment_marking(standard_bundle):
    transmitted, residual = split_bundle_for_partial_transmission(standard_bundle, capacity_bytes=3000)

    assert transmitted.id == "tel-001.part-0"
    assert transmitted.payload_ref == "sensor_data.bin.part-0"
    assert transmitted.is_fragment is True
    assert transmitted.original_bundle_id == "tel-001"
    assert transmitted.fragment_index == 0
    assert transmitted.total_fragments == 2

    assert residual is not None
    assert residual.id == "tel-001.part-1"
    assert residual.payload_ref == "sensor_data.bin.part-1"
    assert residual.is_fragment is True
    assert residual.original_bundle_id == "tel-001"
    assert residual.fragment_index == 1
    assert residual.total_fragments == 2

    for part in (transmitted, residual):
        assert part.type == standard_bundle.type
        assert part.source == standard_bundle.source
        assert part.destination == standard_bundle.destination
        assert part.priority == standard_bundle.priority
        assert part.created_at == standard_bundle.created_at
        assert part.ttl_sec == standard_bundle.ttl_sec
        assert part.status == standard_bundle.status
        assert part.next_hop == standard_bundle.next_hop


def test_partial_split_does_not_mutate_original_bundle(standard_bundle):
    original_id = standard_bundle.id
    original_size = standard_bundle.size_bytes
    original_payload_ref = standard_bundle.payload_ref

    transmitted, residual = split_bundle_for_partial_transmission(standard_bundle, capacity_bytes=3000)

    assert transmitted is not standard_bundle
    assert residual is not None

    assert standard_bundle.id == original_id
    assert standard_bundle.size_bytes == original_size
    assert standard_bundle.payload_ref == original_payload_ref
    assert standard_bundle.is_fragment is False
    assert standard_bundle.original_bundle_id is None
    assert standard_bundle.fragment_index is None
    assert standard_bundle.total_fragments is None