from collections import defaultdict
from typing import Dict, Any, List


class MetricsCollector:
    """Lightweight in-memory metrics collector with a stable snapshot schema."""

    def __init__(self) -> None:
        self.bundles_forwarded_total: Dict[str, int] = defaultdict(int)
        self.bundles_delivered_total: Dict[str, int] = defaultdict(int)
        self.bundles_stored_total: Dict[str, int] = defaultdict(int)
        self.bundles_expired_total: Dict[str, int] = defaultdict(int)
        self.purged_bundle_ids: List[str] = []
        self.recent_purged_ids: List[str] = []
        self.queue_depths: Dict[str, int] = {}
        self.last_queue_depths: Dict[str, int] = {}

        # Wave-19 additive metrics
        self.bundles_dropped_total: Dict[str, int] = defaultdict(int)
        self.dropped_bundle_ids: List[str] = []

    def record_forwarded(self, bundle_type: str) -> None:
        self.bundles_forwarded_total[bundle_type] += 1

    def record_delivered(self, bundle_type: str) -> None:
        self.bundles_delivered_total[bundle_type] += 1

    def record_stored(self, bundle_type: str) -> None:
        self.bundles_stored_total[bundle_type] += 1

    def record_expired(self, bundle_type: str, bundle_id: str | None = None) -> None:
        self.bundles_expired_total[bundle_type] += 1
        if bundle_id:
            if bundle_id not in self.purged_bundle_ids:
                self.purged_bundle_ids.append(bundle_id)
            if bundle_id not in self.recent_purged_ids:
                self.recent_purged_ids.append(bundle_id)

    def set_queue_depth(self, queue_name: str, depth: int) -> None:
        self.queue_depths[queue_name] = depth
        self.last_queue_depths[queue_name] = depth

    def record_dropped(self, bundle_type: str, bundle_id: str) -> None:
        """Record that a bundle was dropped due to queue congestion."""
        self.bundles_dropped_total[bundle_type] += 1
        self.dropped_bundle_ids.append(bundle_id)

    def snapshot(self) -> Dict[str, Any]:
        """Return a point-in-time snapshot of all metrics."""
        return {
            "bundles_forwarded_total": dict(self.bundles_forwarded_total),
            "bundles_delivered_total": dict(self.bundles_delivered_total),
            "bundles_stored_total": dict(self.bundles_stored_total),
            "bundles_expired_total": dict(self.bundles_expired_total),
            "bundles_dropped_total": dict(self.bundles_dropped_total),
            "purged_bundle_ids": list(self.purged_bundle_ids),
            "recent_purged_ids": list(self.recent_purged_ids),
            "dropped_bundle_ids": list(self.dropped_bundle_ids),
            "queue_depths": dict(self.queue_depths),
            "last_queue_depths": dict(self.last_queue_depths),
        }