from typing import List, Set

from router.bundle import Bundle


def _validate_fragments(fragments: List[Bundle]) -> None:
    """Internal helper to strictly validate a collection of fragments."""
    if not fragments:
        raise ValueError("Fragment list is empty.")

    first = fragments[0]
    original_id = first.original_bundle_id
    total_frags = first.total_fragments

    if original_id is None or total_frags is None:
        raise ValueError("Fragments must have original_bundle_id and total_fragments defined.")

    seen_indices: Set[int] = set()

    for f in fragments:
        if not f.is_fragment:
            raise ValueError(f"Bundle {f.id} is not marked as a fragment.")
        if f.original_bundle_id != original_id:
            raise ValueError(f"Mismatched original_bundle_id: {f.original_bundle_id} != {original_id}")
        if f.total_fragments != total_frags:
            raise ValueError(f"Mismatched total_fragments: {f.total_fragments} != {total_frags}")
        if f.fragment_index is None:
            raise ValueError(f"Fragment {f.id} is missing fragment_index.")
        if f.fragment_index in seen_indices:
            raise ValueError(f"Duplicate fragment_index detected: {f.fragment_index}")
        if f.fragment_index < 0 or f.fragment_index >= total_frags:
            raise ValueError(f"Out of bounds fragment_index: {f.fragment_index}")

        seen_indices.add(f.fragment_index)

        if (
            f.source != first.source
            or f.destination != first.destination
            or f.type != first.type
            or f.priority != first.priority
            or f.created_at != first.created_at
            or f.ttl_sec != first.ttl_sec
        ):
            raise ValueError("Inconsistent core metadata (source, dest, priority, etc.) among fragments.")


def can_reassemble(fragments: List[Bundle]) -> bool:
    """
    Check if a collection of fragments is complete and valid for reassembly.
    Returns True if the set is perfect, False otherwise.
    """
    if not fragments:
        return False

    try:
        _validate_fragments(fragments)
    except ValueError:
        return False

    total_expected = fragments[0].total_fragments
    return len(fragments) == total_expected


def reassemble_bundle(fragments: List[Bundle]) -> Bundle:
    """
    Deterministically reassemble a complete set of fragments into the original Bundle.

    Raises:
        ValueError: If the fragment set is empty, incomplete, mixed, or contains invalid metadata.
    """
    if not fragments:
        raise ValueError("Fragment list is empty.")

    if not can_reassemble(fragments):
        raise ValueError("Cannot reassemble: fragment set is incomplete or invalid.")

    sorted_frags = sorted(fragments, key=lambda f: f.fragment_index)
    first = sorted_frags[0]

    total_size = sum(f.size_bytes for f in sorted_frags)
    payload_ref = f"reassembled/{first.original_bundle_id}"

    return Bundle(
        id=first.original_bundle_id,
        type=first.type,
        source=first.source,
        destination=first.destination,
        priority=first.priority,
        created_at=first.created_at,
        ttl_sec=first.ttl_sec,
        size_bytes=total_size,
        payload_ref=payload_ref,
        status=first.status,
        next_hop=first.next_hop,
        is_fragment=False,
        original_bundle_id=None,
        fragment_index=None,
        total_fragments=None,
    )