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
        return {
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