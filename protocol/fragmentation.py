import math
from typing import List

from router.bundle import Bundle


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