from dataclasses import dataclass
from typing import Set

from router.bundle import Bundle


@dataclass(frozen=True)
class DeduplicationConfig:
    """
    Wave-50: Configuration for deterministic bundle deduplication.

    Defaults to disabled to preserve backward compatibility.
    """
    enabled: bool = False
    mode: str = "strict"


@dataclass(frozen=True)
class DeduplicationKey:
    """
    Deterministic identity for a bundle.

    Wave-50 intentionally keeps the identity rule explicit and simple:
    bundle.id is the deduplication identity.
    """
    bundle_id: str

    @classmethod
    def from_bundle(cls, bundle: Bundle) -> "DeduplicationKey":
        return cls(bundle_id=bundle.id)


@dataclass(frozen=True)
class DeduplicationDecision:
    """
    Result of evaluating whether a bundle should be accepted.
    """
    accepted: bool
    reason: str
    key: DeduplicationKey


class BundleDeduplicator:
    """
    Controlled state container for tracking bundle identities seen by a node.

    This class separates:
    - evaluation (pure read against current registry state)
    - registration (explicit mutation after admission)
    """

    def __init__(self, config: DeduplicationConfig | None = None):
        self.config = config or DeduplicationConfig()
        self._seen_keys: Set[DeduplicationKey] = set()

    def evaluate(self, bundle: Bundle) -> DeduplicationDecision:
        """
        Determine whether a bundle should be accepted.

        This method does not mutate registry state.
        """
        key = DeduplicationKey.from_bundle(bundle)

        if not self.config.enabled:
            return DeduplicationDecision(
                accepted=True,
                reason="dedup_disabled",
                key=key,
            )

        if key in self._seen_keys:
            return DeduplicationDecision(
                accepted=False,
                reason="duplicate_rejected",
                key=key,
            )

        return DeduplicationDecision(
            accepted=True,
            reason="first_seen_accepted",
            key=key,
        )

    def register(self, bundle: Bundle) -> None:
        """
        Record that a bundle has been accepted by this node.
        """
        if not self.config.enabled:
            return

        self._seen_keys.add(DeduplicationKey.from_bundle(bundle))