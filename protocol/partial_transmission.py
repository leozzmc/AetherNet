from typing import Optional, Tuple

from router.bundle import Bundle


def split_bundle_for_partial_transmission(
    bundle: Bundle, capacity_bytes: int
) -> Tuple[Bundle, Optional[Bundle]]:
    """
    Wave-27: Partial contact transmission helper.

    Deterministically split a non-fragment bundle into exactly two pieces:
    1. a transmitted portion that fits within the current contact capacity
    2. a residual portion that remains for future transmission

    This helper is intentionally narrow in scope. It explicitly rejects
    bundles that are already fragments in order to avoid recursive fragment
    metadata complexity in this wave.
    """
    if capacity_bytes <= 0:
        raise ValueError("capacity_bytes must be strictly positive for partial transmission.")

    if bundle.is_fragment:
        raise ValueError("Partial transmission of pre-fragmented bundles is not yet supported.")

    if bundle.size_bytes <= capacity_bytes:
        return bundle, None

    transmitted_size = capacity_bytes
    residual_size = bundle.size_bytes - capacity_bytes

    transmitted_part = Bundle(
        id=f"{bundle.id}.part-0",
        type=bundle.type,
        source=bundle.source,
        destination=bundle.destination,
        priority=bundle.priority,
        created_at=bundle.created_at,
        ttl_sec=bundle.ttl_sec,
        size_bytes=transmitted_size,
        payload_ref=f"{bundle.payload_ref}.part-0",
        status=bundle.status,
        next_hop=bundle.next_hop,
        is_fragment=True,
        original_bundle_id=bundle.id,
        fragment_index=0,
        total_fragments=2,
    )

    residual_part = Bundle(
        id=f"{bundle.id}.part-1",
        type=bundle.type,
        source=bundle.source,
        destination=bundle.destination,
        priority=bundle.priority,
        created_at=bundle.created_at,
        ttl_sec=bundle.ttl_sec,
        size_bytes=residual_size,
        payload_ref=f"{bundle.payload_ref}.part-1",
        status=bundle.status,
        next_hop=bundle.next_hop,
        is_fragment=True,
        original_bundle_id=bundle.id,
        fragment_index=1,
        total_fragments=2,
    )

    return transmitted_part, residual_part