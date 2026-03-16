from typing import Optional


class CongestionMetrics:
    """
    Wave-43: Deterministic metrics collector for node storage congestion.
    Tracks overflow events, dropped bundles, and current store utilization.
    """

    def __init__(self, max_store_bytes: Optional[int] = None):
        self.max_store_bytes = max_store_bytes
        self.current_store_bytes: int = 0
        self.overflow_events: int = 0
        self.bundles_dropped: int = 0

    def record_drops(self, dropped_count: int) -> None:
        """Record an overflow event and the number of bundles dropped."""
        if dropped_count > 0:
            self.overflow_events += 1
            self.bundles_dropped += dropped_count

    def update_store_bytes(self, current_bytes: int) -> None:
        """Update the current utilization of the node's store."""
        self.current_store_bytes = current_bytes

    def snapshot(self) -> dict:
        """Produce a deterministic summary of congestion metrics."""
        return {
            "max_store_bytes": self.max_store_bytes,
            "current_store_bytes": self.current_store_bytes,
            "overflow_events": self.overflow_events,
            "bundles_dropped": self.bundles_dropped,
        }