import tempfile

from store.store import DTNStore
from store.retention import expired_bundle_ids, purge_expired
from router.bundle import Bundle


def test_store_purge_expired_bundles():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = DTNStore(tmpdir)

        b1 = Bundle(
            id="valid-1",
            type="tel",
            source="A",
            destination="B",
            priority=1,
            created_at=0,
            ttl_sec=60,
            size_bytes=10,
            payload_ref="payloads/telemetry/valid-1.json",
        )
        b2 = Bundle(
            id="stale-1",
            type="sci",
            source="A",
            destination="B",
            priority=1,
            created_at=0,
            ttl_sec=5,
            size_bytes=10,
            payload_ref="payloads/science/stale-1.json",
        )

        store.save_bundle(b1)
        store.save_bundle(b2)

        expired = expired_bundle_ids(store, current_time=10)
        assert "stale-1" in expired
        assert "valid-1" not in expired

        purged = purge_expired(store, current_time=10)
        assert "stale-1" in purged
        assert store.exists("stale-1") is False
        assert store.exists("valid-1") is True