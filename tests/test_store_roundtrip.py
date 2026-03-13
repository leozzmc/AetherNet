import tempfile
from pathlib import Path
import pytest

from router.bundle import Bundle, BundleStatus
from store.store import DTNStore

@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield DTNStore(tmpdir)

def test_store_save_load_roundtrip(store: DTNStore):
    b = Bundle(
        id="test-123", type="telemetry", source="A", destination="B",
        priority=100, created_at=0, ttl_sec=60, size_bytes=50,
        payload_ref="ref.json", status=BundleStatus.QUEUED, next_hop="C"
    )
    
    store.save_bundle(b)
    
    assert store.exists("test-123")
    assert "test-123" in store.list_bundle_ids()
    
    loaded = store.load_bundle("test-123")
    assert loaded.id == "test-123"
    assert loaded.status == BundleStatus.QUEUED
    assert isinstance(loaded.status, BundleStatus)
    assert loaded.next_hop == "C"

def test_store_delete(store: DTNStore):
    b = Bundle(id="del-1", type="sci", source="A", destination="B", priority=10, created_at=0, ttl_sec=60, size_bytes=50, payload_ref="ref.json")
    store.save_bundle(b)
    
    assert store.delete_bundle("del-1") is True
    assert store.exists("del-1") is False
    assert store.delete_bundle("del-1") is False

def test_store_load_missing(store: DTNStore):
    with pytest.raises(FileNotFoundError):
        store.load_bundle("missing-id")