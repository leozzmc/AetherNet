from collections import defaultdict
from typing import Dict, Any, List


class MetricsCollector:
    """Lightweight in-memory metrics collector with a stable snapshot schema."""

    def __init__(self) -> None:
        self.forwarded_total = defaultdict(int)
        self.delivered_total = defaultdict(int)
        self.stored_total = defaultdict(int)
        self.expired_total = defaultdict(int)
        self.purged_bundle_ids: List[str] = []
        self.queue_depths = defaultdict(int)

    def record_forwarded(self, bundle_type: str) -> None:
        self.forwarded_total[bundle_type] += 1

    def record_delivered(self, bundle_type: str) -> None:
        self.delivered_total[bundle_type] += 1

    def record_stored(self, bundle_type: str) -> None:
        self.stored_total[bundle_type] += 1

    def record_expired(self, bundle_type: str, bundle_id: str | None = None) -> None:
        self.expired_total[bundle_type] += 1
        if bundle_id and bundle_id not in self.purged_bundle_ids:
            self.purged_bundle_ids.append(bundle_id)

    def set_queue_depth(self, queue_name: str, depth: int) -> None:
        self.queue_depths[queue_name] = depth

    def snapshot(self) -> Dict[str, Any]:
        """
        Return a deterministic, JSON-serializable snapshot.

        Backward-compatibility note:
        We expose both old and new field names so older tests and newer
        reporting helpers can coexist.
        """
        queue_depths = dict(self.queue_depths)
        purged_ids = sorted(self.purged_bundle_ids)

        return {
            "bundles_forwarded_total": dict(self.forwarded_total),
            "bundles_delivered_total": dict(self.delivered_total),
            "bundles_stored_total": dict(self.stored_total),
            "bundles_expired_total": dict(self.expired_total),
            # Newer naming
            "purged_bundle_ids": purged_ids,
            "last_queue_depths": queue_depths,
            # Backward-compatible aliases
            "recent_purged_ids": purged_ids,
            "queue_depths": queue_depths,
        }