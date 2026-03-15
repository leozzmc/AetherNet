import pytest
from router.bundle import Bundle, BundleStatus
from protocol.reassembly_buffer import ReassemblyBuffer
from protocol.fragmentation import fragment_bundle
from protocol.reassembly import can_reassemble

@pytest.fixture
def sample_bundle_a() -> Bundle:
    return Bundle("sci-A", "science", "lunar-node", "ground-station", 50, 0, 3600, 2500, "dataA")

@pytest.fixture
def sample_bundle_b() -> Bundle:
    return Bundle("sci-B", "science", "lunar-node", "ground-station", 50, 0, 3600, 1500, "dataB")

def test_buffer_in_order_reassembly(sample_bundle_a):
    buffer = ReassemblyBuffer()
    fragments = fragment_bundle(sample_bundle_a, max_fragment_size_bytes=1000) # 3 fragments
    
    buffer.add(fragments[0])
    buffer.add(fragments[1])
    assert can_reassemble(buffer.get("sci-A")) is False
    
    buffer.add(fragments[2])
    assert can_reassemble(buffer.get("sci-A")) is True

def test_buffer_out_of_order_reassembly(sample_bundle_a):
    buffer = ReassemblyBuffer()
    fragments = fragment_bundle(sample_bundle_a, max_fragment_size_bytes=1000)
    
    buffer.add(fragments[2])
    buffer.add(fragments[0])
    assert can_reassemble(buffer.get("sci-A")) is False
    
    buffer.add(fragments[1])
    assert can_reassemble(buffer.get("sci-A")) is True

def test_buffer_missing_fragment(sample_bundle_a):
    buffer = ReassemblyBuffer()
    fragments = fragment_bundle(sample_bundle_a, max_fragment_size_bytes=1000)
    
    buffer.add(fragments[0])
    buffer.add(fragments[2])
    
    assert can_reassemble(buffer.get("sci-A")) is False
    assert len(buffer.get("sci-A")) == 2

def test_buffer_mixed_fragment_sets(sample_bundle_a, sample_bundle_b):
    buffer = ReassemblyBuffer()
    frags_a = fragment_bundle(sample_bundle_a, max_fragment_size_bytes=1000) # 3 frags
    frags_b = fragment_bundle(sample_bundle_b, max_fragment_size_bytes=1000) # 2 frags
    
    # Interleave arrivals
    buffer.add(frags_a[0])
    buffer.add(frags_b[1])
    buffer.add(frags_a[2])
    buffer.add(frags_b[0]) # B is now complete
    
    assert can_reassemble(buffer.get("sci-B")) is True
    assert can_reassemble(buffer.get("sci-A")) is False
    
    # Complete A
    buffer.add(frags_a[1])
    assert can_reassemble(buffer.get("sci-A")) is True

def test_buffer_remove(sample_bundle_a):
    buffer = ReassemblyBuffer()
    fragments = fragment_bundle(sample_bundle_a, max_fragment_size_bytes=1000)
    buffer.add(fragments[0])
    
    assert len(buffer.get("sci-A")) == 1
    buffer.remove("sci-A")
    assert len(buffer.get("sci-A")) == 0