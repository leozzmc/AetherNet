from dataclasses import dataclass, replace
from typing import Optional, Tuple

from router.bundle import Bundle


@dataclass(frozen=True)
class CustodyAck:
    """
    Wave-29: Deterministic acknowledgment that custody of a bundle
    has been accepted by a new holder.
    """
    bundle_id: str
    from_node: Optional[str]
    to_node: str
    accepted_at: int


def request_custody(bundle: Bundle, requester: str) -> Bundle:
    """
    Return a new Bundle with custody requested by the given requester.
    """
    if bundle.is_fragment:
        raise ValueError("Custody transfer for fragments is not yet supported.")

    if not requester or not requester.strip():
        raise ValueError("Requester cannot be empty.")

    return replace(
        bundle,
        custody_requested=True,
        custody_holder=requester.strip(),
    )


def accept_custody(bundle: Bundle, new_holder: str, accepted_at: int) -> Tuple[Bundle, CustodyAck]:
    """
    Return a new Bundle with custody accepted by a new holder, plus
    a deterministic custody acknowledgment record.
    """
    if bundle.is_fragment:
        raise ValueError("Custody transfer for fragments is not yet supported.")

    if not new_holder or not new_holder.strip():
        raise ValueError("new_holder cannot be empty.")

    if accepted_at < 0:
        raise ValueError("accepted_at must be >= 0.")

    if not bundle.custody_requested:
        raise ValueError(f"Bundle {bundle.id} has not requested custody transfer.")

    previous_holder = bundle.custody_holder
    updated_bundle = replace(bundle, custody_holder=new_holder.strip())

    ack = CustodyAck(
        bundle_id=updated_bundle.id,
        from_node=previous_holder,
        to_node=updated_bundle.custody_holder,
        accepted_at=accepted_at,
    )

    return updated_bundle, ack