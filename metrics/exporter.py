from collections import defaultdict
from typing import Any, Dict, List, Union

from router.bundle import Bundle


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

        # Wave-32 additive fragment metrics
        self.fragments_forwarded_total: Dict[str, int] = defaultdict(int)
        self.fragments_delivered_total: Dict[str, int] = defaultdict(int)
        self.fragments_stored_total: Dict[str, int] = defaultdict(int)
        self.fragments_expired_total: Dict[str, int] = defaultdict(int)
        self.fragments_dropped_total: Dict[str, int] = defaultdict(int)

    def _resolve_bundle_type(self, bundle_or_type: Union[Bundle, str]) -> str:
        if isinstance(bundle_or_type, Bundle):
            return bundle_or_type.type
        return bundle_or_type

    def _is_fragment(self, bundle_or_type: Union[Bundle, str]) -> bool:
        return isinstance(bundle_or_type, Bundle) and bundle_or_type.is_fragment

    def _resolve_bundle_id(self, bundle_or_type: Union[Bundle, str], bundle_id: str | None) -> str | None:
        if bundle_id is not None:
            return bundle_id
        if isinstance(bundle_or_type, Bundle):
            return bundle_or_type.id
        return None

    def record_forwarded(self, bundle_or_type: Union[Bundle, str]) -> None:
        bundle_type = self._resolve_bundle_type(bundle_or_type)
        if self._is_fragment(bundle_or_type):
            self.fragments_forwarded_total[bundle_type] += 1
        else:
            self.bundles_forwarded_total[bundle_type] += 1

    def record_delivered(self, bundle_or_type: Union[Bundle, str]) -> None:
        bundle_type = self._resolve_bundle_type(bundle_or_type)
        if self._is_fragment(bundle_or_type):
            self.fragments_delivered_total[bundle_type] += 1
        else:
            self.bundles_delivered_total[bundle_type] += 1

    def record_stored(self, bundle_or_type: Union[Bundle, str]) -> None:
        bundle_type = self._resolve_bundle_type(bundle_or_type)
        if self._is_fragment(bundle_or_type):
            self.fragments_stored_total[bundle_type] += 1
        else:
            self.bundles_stored_total[bundle_type] += 1

    def record_expired(self, bundle_or_type: Union[Bundle, str], bundle_id: str | None = None) -> None:
        bundle_type = self._resolve_bundle_type(bundle_or_type)
        resolved_bundle_id = self._resolve_bundle_id(bundle_or_type, bundle_id)

        if self._is_fragment(bundle_or_type):
            self.fragments_expired_total[bundle_type] += 1
        else:
            self.bundles_expired_total[bundle_type] += 1

        if resolved_bundle_id:
            if resolved_bundle_id not in self.purged_bundle_ids:
                self.purged_bundle_ids.append(resolved_bundle_id)
            if resolved_bundle_id not in self.recent_purged_ids:
                self.recent_purged_ids.append(resolved_bundle_id)

    def set_queue_depth(self, queue_name: str, depth: int) -> None:
        self.queue_depths[queue_name] = depth
        self.last_queue_depths[queue_name] = depth

    def record_dropped(self, bundle_or_type: Union[Bundle, str], bundle_id: str) -> None:
        """Record that a bundle or fragment was dropped due to queue congestion."""
        bundle_type = self._resolve_bundle_type(bundle_or_type)

        if self._is_fragment(bundle_or_type):
            self.fragments_dropped_total[bundle_type] += 1
        else:
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
            "fragments_forwarded_total": dict(self.fragments_forwarded_total),
            "fragments_delivered_total": dict(self.fragments_delivered_total),
            "fragments_stored_total": dict(self.fragments_stored_total),
            "fragments_expired_total": dict(self.fragments_expired_total),
            "fragments_dropped_total": dict(self.fragments_dropped_total),
            "purged_bundle_ids": list(self.purged_bundle_ids),
            "recent_purged_ids": list(self.recent_purged_ids),
            "dropped_bundle_ids": list(self.dropped_bundle_ids),
            "queue_depths": dict(self.queue_depths),
            "last_queue_depths": dict(self.last_queue_depths),
        }