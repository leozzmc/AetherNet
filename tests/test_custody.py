import pytest

from protocol.custody import CustodyAck, accept_custody, request_custody
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


def test_request_custody_sets_fields_correctly(standard_bundle):
    new_bundle = request_custody(standard_bundle, requester="lunar-node")

    assert new_bundle.custody_requested is True
    assert new_bundle.custody_holder == "lunar-node"


def test_request_custody_preserves_metadata(standard_bundle):
    new_bundle = request_custody(standard_bundle, requester="lunar-node")

    assert new_bundle.id == standard_bundle.id
    assert new_bundle.size_bytes == standard_bundle.size_bytes
    assert new_bundle.priority == standard_bundle.priority
    assert new_bundle.status == standard_bundle.status
    assert new_bundle.payload_ref == standard_bundle.payload_ref
    assert new_bundle.next_hop == standard_bundle.next_hop


def test_request_custody_does_not_mutate_original(standard_bundle):
    new_bundle = request_custody(standard_bundle, requester="lunar-node")

    assert new_bundle is not standard_bundle
    assert standard_bundle.custody_requested is False
    assert standard_bundle.custody_holder is None


def test_request_custody_rejects_fragments(fragment_bundle):
    with pytest.raises(ValueError, match="not yet supported"):
        request_custody(fragment_bundle, requester="lunar-node")


def test_request_custody_rejects_empty_requester(standard_bundle):
    with pytest.raises(ValueError, match="cannot be empty"):
        request_custody(standard_bundle, requester="")

    with pytest.raises(ValueError, match="cannot be empty"):
        request_custody(standard_bundle, requester="   ")


@pytest.fixture
def custody_bundle(standard_bundle) -> Bundle:
    return request_custody(standard_bundle, requester="lunar-node")


def test_accept_custody_updates_holder_and_returns_ack(custody_bundle):
    new_bundle, ack = accept_custody(custody_bundle, new_holder="leo-relay", accepted_at=10)

    assert new_bundle.custody_holder == "leo-relay"
    assert new_bundle.custody_requested is True

    assert isinstance(ack, CustodyAck)
    assert ack.bundle_id == "tel-001"
    assert ack.from_node == "lunar-node"
    assert ack.to_node == "leo-relay"
    assert ack.accepted_at == 10


def test_accept_custody_preserves_metadata(custody_bundle):
    new_bundle, _ = accept_custody(custody_bundle, new_holder="leo-relay", accepted_at=10)

    assert new_bundle.id == custody_bundle.id
    assert new_bundle.size_bytes == custody_bundle.size_bytes
    assert new_bundle.priority == custody_bundle.priority
    assert new_bundle.status == custody_bundle.status
    assert new_bundle.payload_ref == custody_bundle.payload_ref
    assert new_bundle.next_hop == custody_bundle.next_hop
    assert new_bundle.source == custody_bundle.source
    assert new_bundle.destination == custody_bundle.destination


def test_accept_custody_does_not_mutate_original(custody_bundle):
    original_holder = custody_bundle.custody_holder
    new_bundle, _ = accept_custody(custody_bundle, new_holder="leo-relay", accepted_at=10)

    assert new_bundle is not custody_bundle
    assert custody_bundle.custody_holder == original_holder


def test_accept_custody_rejects_fragments(fragment_bundle):
    fragment_with_custody = Bundle(
        id=fragment_bundle.id,
        type=fragment_bundle.type,
        source=fragment_bundle.source,
        destination=fragment_bundle.destination,
        priority=fragment_bundle.priority,
        created_at=fragment_bundle.created_at,
        ttl_sec=fragment_bundle.ttl_sec,
        size_bytes=fragment_bundle.size_bytes,
        payload_ref=fragment_bundle.payload_ref,
        status=fragment_bundle.status,
        next_hop=fragment_bundle.next_hop,
        is_fragment=fragment_bundle.is_fragment,
        original_bundle_id=fragment_bundle.original_bundle_id,
        fragment_index=fragment_bundle.fragment_index,
        total_fragments=fragment_bundle.total_fragments,
        custody_requested=True,
        custody_holder="lunar-node",
    )

    with pytest.raises(ValueError, match="not yet supported"):
        accept_custody(fragment_with_custody, new_holder="leo-relay", accepted_at=10)


def test_accept_custody_rejects_empty_new_holder(custody_bundle):
    with pytest.raises(ValueError, match="cannot be empty"):
        accept_custody(custody_bundle, new_holder="", accepted_at=10)

    with pytest.raises(ValueError, match="cannot be empty"):
        accept_custody(custody_bundle, new_holder="   ", accepted_at=10)


def test_accept_custody_rejects_negative_accepted_at(custody_bundle):
    with pytest.raises(ValueError, match="accepted_at must be >= 0"):
        accept_custody(custody_bundle, new_holder="leo-relay", accepted_at=-1)


def test_accept_custody_rejects_bundles_without_request(standard_bundle):
    with pytest.raises(ValueError, match="has not requested custody"):
        accept_custody(standard_bundle, new_holder="leo-relay", accepted_at=10)