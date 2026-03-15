import pytest
from router.bundle import Bundle
from protocol.reassembly import can_reassemble, reassemble_bundle
from protocol.fragmentation import fragment_bundle

@pytest.fixture
def original_bundle() -> Bundle:
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

@pytest.fixture
def fragments(original_bundle) -> list[Bundle]:
    # Creates 3 fragments: 1000, 1000, 500 bytes
    return fragment_bundle(original_bundle, max_fragment_size_bytes=1000)

def test_successful_out_of_order_reassembly(fragments, original_bundle):
    # Shuffle the arrival order: [Frag 2, Frag 0, Frag 1]
    shuffled = [fragments[2], fragments[0], fragments[1]]

    assert can_reassemble(shuffled) is True

    reassembled = reassemble_bundle(shuffled)

    # Validate core restoration
    assert reassembled.id == original_bundle.id
    assert reassembled.size_bytes == original_bundle.size_bytes
    assert reassembled.payload_ref == f"reassembled/{original_bundle.id}"
    
    # Validate metadata clearance
    assert reassembled.is_fragment is False
    assert reassembled.original_bundle_id is None
    assert reassembled.total_fragments is None
    assert reassembled.fragment_index is None

    # Validate inherited fields
    assert reassembled.source == original_bundle.source
    assert reassembled.destination == original_bundle.destination
    assert reassembled.priority == original_bundle.priority
    assert reassembled.type == original_bundle.type

def test_incomplete_fragments_fails(fragments):
    incomplete = [fragments[0], fragments[1]] # Missing frag 2
    
    assert can_reassemble(incomplete) is False
    with pytest.raises(ValueError, match="incomplete or invalid"):
        reassemble_bundle(incomplete)

def test_mismatched_original_id_fails(fragments):
    rogue_frag = Bundle(
        id="sci-002.frag-0",
        type="science",
        source="lunar-node",
        destination="ground-station",
        priority=50,
        created_at=10,
        ttl_sec=3600,
        size_bytes=1000,
        payload_ref="rogue.bin.frag-0",
        is_fragment=True,
        original_bundle_id="sci-002",
        fragment_index=0,
        total_fragments=3,
    )
    mixed = [fragments[0], fragments[1], rogue_frag]

    assert can_reassemble(mixed) is False

def test_inconsistent_metadata_fails(fragments):
    # Mutate one fragment's priority to simulate corruption or a bug
    fragments[1].priority = 99
    assert can_reassemble(fragments) is False

def test_duplicate_index_fails(fragments):
    duplicates = [fragments[0], fragments[0], fragments[2]]
    assert can_reassemble(duplicates) is False

def test_empty_list_fails():
    assert can_reassemble([]) is False
    with pytest.raises(ValueError, match="empty"):
        reassemble_bundle([])