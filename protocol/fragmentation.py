import math
from typing import List

from router.bundle import Bundle
from router.contact_manager import Contact


def compute_contact_capacity_bytes(contact: Contact) -> int:
    """
    Calculate the theoretical maximum byte capacity of a contact window.

    Formula:
        capacity_bytes = int((bandwidth_kbit * 1000 / 8) * duration_sec)

    This is a Wave-26 planning primitive only. It does not yet model
    partial transmission across multiple contacts.
    """
    duration_sec = contact.end_time - contact.start_time
    if duration_sec <= 0:
        return 0

    bytes_per_sec = (contact.bandwidth_kbit * 1000) / 8
    return int(bytes_per_sec * duration_sec)


def fragment_bundle(bundle: Bundle, max_fragment_size_bytes: int) -> List[Bundle]:
    """
    Deterministically split an oversized bundle into multiple fragments.

    If the original bundle already fits, return [bundle].
    """
    if max_fragment_size_bytes <= 0:
        raise ValueError("max_fragment_size_bytes must be strictly positive")

    if bundle.size_bytes <= max_fragment_size_bytes:
        return [bundle]

    total_fragments = math.ceil(bundle.size_bytes / max_fragment_size_bytes)
    fragments: List[Bundle] = []
    bytes_remaining = bundle.size_bytes

    for i in range(total_fragments):
        frag_size = min(max_fragment_size_bytes, bytes_remaining)
        bytes_remaining -= frag_size

        frag_id = f"{bundle.id}.frag-{i}"
        frag_payload_ref = f"{bundle.payload_ref}.frag-{i}"

        fragment = Bundle(
            id=frag_id,
            type=bundle.type,
            source=bundle.source,
            destination=bundle.destination,
            priority=bundle.priority,
            created_at=bundle.created_at,
            ttl_sec=bundle.ttl_sec,
            size_bytes=frag_size,
            payload_ref=frag_payload_ref,
            status=bundle.status,
            next_hop=bundle.next_hop,
            is_fragment=True,
            original_bundle_id=bundle.id,
            fragment_index=i,
            total_fragments=total_fragments,
        )
        fragments.append(fragment)

    return fragments


def fragment_bundle_contact_aware(bundle: Bundle, contact: Contact) -> List[Bundle]:
    """
    Wave-26: Contact-aware fragmentation.

    Derive the fragment size limit from the contact window's theoretical
    byte capacity, then reuse the existing deterministic fragmentation logic.

    Note:
        This does NOT yet implement partial contact transmission.
        That belongs to Wave-27.
    """
    capacity_bytes = compute_contact_capacity_bytes(contact)

    if capacity_bytes <= 0:
        raise ValueError("Contact capacity must be strictly positive to fragment a bundle.")

    if bundle.size_bytes <= capacity_bytes:
        return [bundle]

    return fragment_bundle(bundle, max_fragment_size_bytes=capacity_bytes)