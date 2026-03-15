import pytest
from router.bundle import Bundle, BundleStatus
from protocol.fragmentation import fragment_bundle
from protocol.bundle import BundleProtocolV1

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
        payload_ref="data.bin"
    )

def test_no_fragmentation_needed(oversized_bundle):
    # Bundle fits perfectly
    result = fragment_bundle(oversized_bundle, max_fragment_size_bytes=3000)
    assert len(result) == 1
    assert result[0] is oversized_bundle
    assert result[0].is_fragment is False

def test_deterministic_fragmentation(oversized_bundle):
    # 2500 bytes / 1000 max size = 3 fragments (1000, 1000, 500)
    fragments = fragment_bundle(oversized_bundle, max_fragment_size_bytes=1000)
    
    assert len(fragments) == 3
    
    # Verify sizes
    assert fragments[0].size_bytes == 1000
    assert fragments[1].size_bytes == 1000
    assert fragments[2].size_bytes == 500
    
    # Verify total size conservation
    assert sum(f.size_bytes for f in fragments) == oversized_bundle.size_bytes
    
    # Verify exact deterministic metadata
    for i, frag in enumerate(fragments):
        assert frag.is_fragment is True
        assert frag.original_bundle_id == "sci-001"
        assert frag.total_fragments == 3
        assert frag.fragment_index == i
        assert frag.id == f"sci-001.frag-{i}"
        assert frag.payload_ref == f"data.bin.frag-{i}"
        
        # Verify inherited fields
        assert frag.type == "science"
        assert frag.priority == 50
        assert frag.destination == "ground-station"

def test_fragment_serialization_roundtrip(oversized_bundle):
    fragments = fragment_bundle(oversized_bundle, max_fragment_size_bytes=1000)
    frag_0 = fragments[0]
    
    # Convert to dict
    data = BundleProtocolV1.to_dict(frag_0)
    assert data["is_fragment"] is True
    assert data["fragment_index"] == 0
    
    # Restore from dict
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