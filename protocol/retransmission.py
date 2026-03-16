from dataclasses import replace

from router.bundle import Bundle, BundleStatus


def is_fragment_retransmittable(fragment: Bundle, current_time: int) -> bool:
    """
    Wave-30: Determine whether a fragment is eligible for retransmission.

    Retransmission is strictly scoped to fragment bundles in this wave.
    A fragment is not eligible if it is expired, already delivered, or
    if the provided simulation time is negative.
    """
    if not fragment.is_fragment:
        raise ValueError("Retransmission is only supported for fragment bundles.")

    if current_time < 0:
        return False

    if fragment.status == BundleStatus.DELIVERED:
        return False

    if fragment.status == BundleStatus.EXPIRED:
        return False

    if fragment.is_expired(current_time):
        return False

    return True


def create_fragment_retransmission(fragment: Bundle, current_time: int) -> Bundle:
    """
    Create a deterministic, retransmission-ready copy of a fragment.

    The returned fragment preserves its original fragment identity fields
    but increments retransmission_count and resets status to QUEUED.
    The input fragment is not mutated.
    """
    if not fragment.is_fragment:
        raise ValueError("Retransmission is only supported for fragment bundles.")

    if not is_fragment_retransmittable(fragment, current_time):
        raise ValueError(f"Fragment {fragment.id} is not eligible for retransmission at t={current_time}.")

    return replace(
        fragment,
        status=BundleStatus.QUEUED,
        retransmission_count=fragment.retransmission_count + 1,
    )