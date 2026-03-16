from typing import Optional


class CongestionMetrics:
    """
    Wave-43/45: Deterministic metrics collector for node storage pressure.
    Tracks overflow events, dropped bundles/bytes, and utilization peaks.
    """

    def __init__(
        self, 
        max_store_bytes: Optional[int] = None, 
        eviction_policy_name: str = "DropLowestPriorityPolicy"
    ):
        self.max_store_bytes = max_store_bytes
        self.eviction_policy_name = eviction_policy_name
        self.current_store_bytes: int = 0
        self.peak_store_bytes: int = 0
        self.overflow_events: int = 0
        self.bundles_dropped: int = 0
        self.dropped_bytes: int = 0

    def record_drops(self, dropped_count: int, dropped_bytes: int) -> None:
        """Record an overflow event and the amount of data dropped."""
        if dropped_count > 0:
            self.overflow_events += 1
            self.bundles_dropped += dropped_count
            self.dropped_bytes += dropped_bytes

    def update_store_bytes(self, current_bytes: int) -> None:
        """Update the current utilization and track the historical peak."""
        self.current_store_bytes = current_bytes
        if self.current_store_bytes > self.peak_store_bytes:
            self.peak_store_bytes = self.current_store_bytes

    def snapshot(self) -> dict:
        """Produce a deterministic summary of storage pressure metrics."""
        utilization_ratio = 0.0
        if self.max_store_bytes and self.max_store_bytes > 0:
            utilization_ratio = self.current_store_bytes / self.max_store_bytes

        return {
            "eviction_policy": self.eviction_policy_name,
            "max_store_bytes": self.max_store_bytes,
            "current_store_bytes": self.current_store_bytes,
            "peak_store_bytes": self.peak_store_bytes,
            "store_utilization_ratio": round(utilization_ratio, 4),
            "overflow_events": self.overflow_events,
            "bundles_dropped": self.bundles_dropped,
            "dropped_bytes": self.dropped_bytes,
        }