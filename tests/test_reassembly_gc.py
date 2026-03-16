import pytest

from protocol.reassembly_buffer import ReassemblyBuffer
from router.bundle import Bundle, BundleStatus


@pytest.fixture
def make_fragment():
    """Helper to generate deterministic test fragments."""

    def _make(
        frag_id: str,
        original_id: str,
        created_at: int,
        ttl_sec: int,
        fragment_index: int = 0,
        total_fragments: int = 3,
    ) -> Bundle:
        return Bundle(
            id=frag_id,
            type="science",
            source="lunar-node",
            destination="ground-station",
            priority=50,
            created_at=created_at,
            ttl_sec=ttl_sec,
            size_bytes=1000,
            payload_ref=f"data.bin.{frag_id}",
            status=BundleStatus.FORWARDING,
            is_fragment=True,
            original_bundle_id=original_id,
            fragment_index=fragment_index,
            total_fragments=total_fragments,
        )

    return _make


def test_empty_buffer_returns_empty_list():
    buffer = ReassemblyBuffer()
    removed = buffer.collect_garbage(current_time=10)
    assert removed == []


def test_negative_current_time_raises_value_error():
    buffer = ReassemblyBuffer()
    with pytest.raises(ValueError, match="current_time must be >= 0"):
        buffer.collect_garbage(current_time=-5)


def test_complete_non_expired_fragment_set_is_preserved(make_fragment):
    buffer = ReassemblyBuffer()

    frag1 = make_fragment("f1", "bundle-1", created_at=10, ttl_sec=100, fragment_index=0)
    frag2 = make_fragment("f2", "bundle-1", created_at=10, ttl_sec=100, fragment_index=1)

    buffer.add(frag1)
    buffer.add(frag2)

    removed = buffer.collect_garbage(current_time=50)

    assert removed == []
    assert len(buffer.get("bundle-1")) == 2


def test_incomplete_non_expired_fragment_set_is_preserved(make_fragment):
    buffer = ReassemblyBuffer()

    frag1 = make_fragment("f1", "bundle-incomplete", created_at=10, ttl_sec=100, fragment_index=0)
    buffer.add(frag1)

    removed = buffer.collect_garbage(current_time=50)

    assert removed == []
    assert len(buffer.get("bundle-incomplete")) == 1


def test_any_expired_fragment_removes_whole_set(make_fragment):
    buffer = ReassemblyBuffer()

    frag1 = make_fragment("f1", "bundle-mixed", created_at=10, ttl_sec=100, fragment_index=0)
    frag2 = make_fragment("f2", "bundle-mixed", created_at=10, ttl_sec=50, fragment_index=1)

    buffer.add(frag1)
    buffer.add(frag2)

    removed = buffer.collect_garbage(current_time=65)

    assert removed == ["bundle-mixed"]
    assert len(buffer.get("bundle-mixed")) == 0


def test_multiple_expired_sets_removed_together_sorted(make_fragment):
    buffer = ReassemblyBuffer()

    buffer.add(make_fragment("c1", "bundle-C", created_at=0, ttl_sec=50, fragment_index=0))
    buffer.add(make_fragment("a1", "bundle-A", created_at=0, ttl_sec=40, fragment_index=0))
    buffer.add(make_fragment("b1", "bundle-B", created_at=0, ttl_sec=100, fragment_index=0))

    removed = buffer.collect_garbage(current_time=60)

    assert removed == ["bundle-A", "bundle-C"]
    assert len(buffer.get("bundle-A")) == 0
    assert len(buffer.get("bundle-C")) == 0
    assert len(buffer.get("bundle-B")) == 1


def test_non_expired_sets_remain_accessible_after_gc(make_fragment):
    buffer = ReassemblyBuffer()

    buffer.add(make_fragment("exp1", "expired-set", created_at=0, ttl_sec=10, fragment_index=0))
    buffer.add(make_fragment("good1", "good-set", created_at=0, ttl_sec=100, fragment_index=0))

    removed = buffer.collect_garbage(current_time=50)

    assert removed == ["expired-set"]
    assert len(buffer.get("expired-set")) == 0

    remaining = buffer.get("good-set")
    assert len(remaining) == 1
    assert remaining[0].id == "good1"