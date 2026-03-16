from dataclasses import dataclass
from enum import Enum
from typing import Optional


class BundleStatus(str, Enum):
    QUEUED = "queued"
    STORED = "stored"
    FORWARDING = "forwarding"
    DELIVERED = "delivered"
    EXPIRED = "expired"
    FAILED = "failed"


_ALLOWED_TRANSITIONS = {
    BundleStatus.QUEUED: {BundleStatus.STORED, BundleStatus.FORWARDING, BundleStatus.EXPIRED, BundleStatus.FAILED},
    BundleStatus.STORED: {BundleStatus.FORWARDING, BundleStatus.EXPIRED, BundleStatus.FAILED},
    BundleStatus.FORWARDING: {BundleStatus.DELIVERED, BundleStatus.STORED, BundleStatus.EXPIRED, BundleStatus.FAILED},
    BundleStatus.DELIVERED: set(),
    BundleStatus.EXPIRED: set(),
    BundleStatus.FAILED: set(),
}


@dataclass
class Bundle:
    id: str
    type: str
    source: str
    destination: str
    priority: int
    created_at: int
    ttl_sec: int
    size_bytes: int
    payload_ref: str
    status: BundleStatus = BundleStatus.QUEUED
    next_hop: Optional[str] = None

    # Wave-23 additive fragmentation metadata
    is_fragment: bool = False
    original_bundle_id: Optional[str] = None
    fragment_index: Optional[int] = None
    total_fragments: Optional[int] = None

    # Wave-29 additive custody transfer metadata
    custody_requested: bool = False
    custody_holder: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Bundle id must not be empty.")
        if not self.type.strip():
            raise ValueError("Bundle type must not be empty.")
        if not self.source.strip():
            raise ValueError("Bundle source must not be empty.")
        if not self.destination.strip():
            raise ValueError("Bundle destination must not be empty.")
        if self.priority < 0:
            raise ValueError("Bundle priority must be >= 0.")
        if self.created_at < 0:
            raise ValueError("Bundle created_at must be >= 0.")
        if self.ttl_sec < 0:
            raise ValueError("Bundle ttl_sec must be >= 0.")
        if self.size_bytes < 0:
            raise ValueError("Bundle size_bytes must be >= 0.")
        if not self.payload_ref.strip():
            raise ValueError("Bundle payload_ref must not be empty.")

        if self.is_fragment:
            if self.original_bundle_id is None or not self.original_bundle_id.strip():
                raise ValueError("Fragment bundles must define original_bundle_id.")
            if self.fragment_index is None or self.fragment_index < 0:
                raise ValueError("Fragment bundles must define fragment_index >= 0.")
            if self.total_fragments is None or self.total_fragments <= 0:
                raise ValueError("Fragment bundles must define total_fragments > 0.")
            if self.fragment_index >= self.total_fragments:
                raise ValueError("fragment_index must be less than total_fragments.")

    def is_expired(self, current_time: int) -> bool:
        """A bundle is expired when elapsed time is greater than or equal to ttl_sec."""
        if current_time < self.created_at:
            return False
        return (current_time - self.created_at) >= self.ttl_sec

    def transition(self, new_status: BundleStatus) -> None:
        allowed = _ALLOWED_TRANSITIONS[self.status]
        if new_status not in allowed and new_status != self.status:
            raise ValueError(
                f"Invalid status transition: {self.status.value} -> {new_status.value}"
            )
        self.status = new_status

    def to_dict(self) -> dict:
        data = {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "destination": self.destination,
            "next_hop": self.next_hop,
            "priority": self.priority,
            "created_at": self.created_at,
            "ttl_sec": self.ttl_sec,
            "size_bytes": self.size_bytes,
            "payload_ref": self.payload_ref,
            "status": self.status.value,
        }

        if self.is_fragment:
            data["is_fragment"] = self.is_fragment
            data["original_bundle_id"] = self.original_bundle_id
            data["fragment_index"] = self.fragment_index
            data["total_fragments"] = self.total_fragments

        return data