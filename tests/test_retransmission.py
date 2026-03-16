from dataclasses import replace

import pytest

from protocol.retransmission import create_fragment_retransmission, is_fragment_retransmittable
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
        status=BundleStatus.FORWARDING,
        retransmission_count=0,
    )


# --- Bundle validation test ---


def test_bundle_rejects_negative_retransmission_count():
    with pytest.raises(ValueError, match="retransmission_count must be >= 0"):
        Bundle(
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
            retransmission_count=-1,
        )


# --- is_fragment_retransmittable tests ---


def test_rejects_non_fragment_bundles(standard_bundle):
    with pytest.raises(ValueError, match="only supported for fragment bundles"):
        is_fragment_retransmittable(standard_bundle, current_time=10)


def test_negative_current_time_returns_false(fragment_bundle):
    assert is_fragment_retransmittable(fragment_bundle, current_time=-5) is False


def test_delivered_fragment_is_not_retransmittable(fragment_bundle):
    delivered_fragment = replace(fragment_bundle, status=BundleStatus.DELIVERED)
    assert is_fragment_retransmittable(delivered_fragment, current_time=10) is False


def test_expired_status_fragment_is_not_retransmittable(fragment_bundle):
    expired_fragment = replace(fragment_bundle, status=BundleStatus.EXPIRED)
    assert is_fragment_retransmittable(expired_fragment, current_time=10) is False


def test_time_expired_fragment_is_not_retransmittable(fragment_bundle):
    # created_at=5, ttl=3600 -> expires at 3605
    assert is_fragment_retransmittable(fragment_bundle, current_time=4000) is False


def test_valid_fragment_is_retransmittable(fragment_bundle):
    assert is_fragment_retransmittable(fragment_bundle, current_time=10) is True


# --- create_fragment_retransmission tests ---


def test_create_rejects_non_fragment_bundles(standard_bundle):
    with pytest.raises(ValueError, match="only supported for fragment bundles"):
        create_fragment_retransmission(standard_bundle, current_time=10)


def test_create_rejects_non_retransmittable_fragments(fragment_bundle):
    delivered_fragment = replace(fragment_bundle, status=BundleStatus.DELIVERED)
    with pytest.raises(ValueError, match="not eligible for retransmission"):
        create_fragment_retransmission(delivered_fragment, current_time=10)


def test_create_increments_count_and_resets_status(fragment_bundle):
    new_frag = create_fragment_retransmission(fragment_bundle, current_time=10)

    assert new_frag.retransmission_count == 1
    assert new_frag.status == BundleStatus.QUEUED

    forwarding_again = replace(new_frag, status=BundleStatus.FORWARDING)
    newer_frag = create_fragment_retransmission(forwarding_again, current_time=20)

    assert newer_frag.retransmission_count == 2
    assert newer_frag.status == BundleStatus.QUEUED


def test_create_preserves_fragment_metadata(fragment_bundle):
    new_frag = create_fragment_retransmission(fragment_bundle, current_time=10)

    assert new_frag.id == fragment_bundle.id
    assert new_frag.original_bundle_id == fragment_bundle.original_bundle_id
    assert new_frag.fragment_index == fragment_bundle.fragment_index
    assert new_frag.total_fragments == fragment_bundle.total_fragments

    assert new_frag.type == fragment_bundle.type
    assert new_frag.source == fragment_bundle.source
    assert new_frag.destination == fragment_bundle.destination
    assert new_frag.priority == fragment_bundle.priority
    assert new_frag.created_at == fragment_bundle.created_at
    assert new_frag.ttl_sec == fragment_bundle.ttl_sec
    assert new_frag.size_bytes == fragment_bundle.size_bytes
    assert new_frag.payload_ref == fragment_bundle.payload_ref
    assert new_frag.next_hop == fragment_bundle.next_hop


def test_create_does_not_mutate_original(fragment_bundle):
    original_status = fragment_bundle.status
    original_count = fragment_bundle.retransmission_count

    new_frag = create_fragment_retransmission(fragment_bundle, current_time=10)

    assert new_frag is not fragment_bundle
    assert fragment_bundle.status == original_status
    assert fragment_bundle.retransmission_count == original_count