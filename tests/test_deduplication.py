import json

from router.app import AetherRouter
from router.bundle import Bundle
from router.contact_manager import ContactManager
from router.deduplication import (
    BundleDeduplicator,
    DeduplicationConfig,
    DeduplicationKey,
)


def make_bundle(b_id: str, destination: str = "node-B") -> Bundle:
    return Bundle(
        id=b_id,
        type="data",
        source="node-A",
        destination=destination,
        priority=100,
        created_at=0,
        ttl_sec=3600,
        size_bytes=100,
        payload_ref="ref",
    )


def make_contact_manager(tmp_path):
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps({"simulation_duration_sec": 100, "contacts": []}),
        encoding="utf-8",
    )
    return ContactManager(str(plan_path))


def test_deduplication_disabled_preserves_existing_behavior():
    config = DeduplicationConfig(enabled=False)
    dedup = BundleDeduplicator(config)

    b1 = make_bundle("bundle-1")

    decision1 = dedup.evaluate(b1)
    assert decision1.accepted is True
    assert decision1.reason == "dedup_disabled"

    dedup.register(b1)

    decision2 = dedup.evaluate(b1)
    assert decision2.accepted is True
    assert decision2.reason == "dedup_disabled"


def test_deduplication_key_generation_is_stable():
    b1 = make_bundle("bundle-alpha")
    b2 = make_bundle("bundle-alpha")

    key1 = DeduplicationKey.from_bundle(b1)
    key2 = DeduplicationKey.from_bundle(b2)

    assert key1 == key2
    assert key1.bundle_id == "bundle-alpha"


def test_deduplicator_accepts_first_and_rejects_duplicate():
    config = DeduplicationConfig(enabled=True)
    dedup = BundleDeduplicator(config)

    b1 = make_bundle("bundle-1")

    decision1 = dedup.evaluate(b1)
    assert decision1.accepted is True
    assert decision1.reason == "first_seen_accepted"

    dedup.register(b1)

    b1_copy = make_bundle("bundle-1")
    decision2 = dedup.evaluate(b1_copy)

    assert decision2.accepted is False
    assert decision2.reason == "duplicate_rejected"


def test_deduplicator_does_not_confuse_distinct_bundles():
    config = DeduplicationConfig(enabled=True)
    dedup = BundleDeduplicator(config)

    b1 = make_bundle("bundle-1")
    b2 = make_bundle("bundle-2")

    dedup.register(b1)

    decision2 = dedup.evaluate(b2)
    assert decision2.accepted is True
    assert decision2.reason == "first_seen_accepted"


def test_router_integration_with_deduplication(tmp_path):
    config = DeduplicationConfig(enabled=True)
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        deduplication_config=config,
        store_capacity_bytes=500,
    )

    b1 = make_bundle("bundle-1")
    b1_copy = make_bundle("bundle-1")

    dropped_1 = router.store_bundle(b1)
    assert dropped_1 == []
    assert len(router.store) == 1

    dropped_2 = router.store_bundle(b1_copy)
    assert len(dropped_2) == 1
    assert dropped_2[0].id == "bundle-1"
    assert len(router.store) == 1


def test_router_deduplication_does_not_break_single_path_routing(tmp_path):
    router = AetherRouter(
        contact_manager=make_contact_manager(tmp_path),
        deduplication_config=DeduplicationConfig(enabled=True),
    )

    assert router.get_next_hop("lunar-node", "ground-station") == "leo-relay"