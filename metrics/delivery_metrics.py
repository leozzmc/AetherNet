from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class DeliveryRecord:
    """
    Wave-51: Immutable record of bundle delivery history.
    """
    bundle_id: str
    first_delivery_time: int
    delivery_count: int


class DeliveryMetrics:
    """
    Wave-51: Deterministic delivery accounting layer.

    Tracks:
    - first delivery vs duplicate delivery
    - unique delivered bundle count
    - total delivery event count
    - duplicate delivery count

    This is intentionally separate from:
    - routing
    - store deduplication
    - congestion metrics
    """

    def __init__(self, expected_total_bundles: int = 0):
        self.expected_total_bundles = expected_total_bundles
        self._records: Dict[str, DeliveryRecord] = {}
        self.total_delivered: int = 0
        self.duplicate_deliveries: int = 0

    def record_delivery(self, bundle_id: str, current_time: int) -> str:
        """
        Record a successful final delivery event.

        Returns:
        - "first_delivery"
        - "duplicate_delivery"
        """
        self.total_delivered += 1

        if bundle_id in self._records:
            existing = self._records[bundle_id]
            self.duplicate_deliveries += 1
            self._records[bundle_id] = DeliveryRecord(
                bundle_id=bundle_id,
                first_delivery_time=existing.first_delivery_time,
                delivery_count=existing.delivery_count + 1,
            )
            return "duplicate_delivery"

        self._records[bundle_id] = DeliveryRecord(
            bundle_id=bundle_id,
            first_delivery_time=current_time,
            delivery_count=1,
        )
        return "first_delivery"

    def snapshot(self) -> dict:
        """
        Produce a deterministic delivery summary.
        """
        unique_delivered = len(self._records)
        delivery_ratio = 0.0

        if self.expected_total_bundles > 0:
            delivery_ratio = unique_delivered / self.expected_total_bundles

        return {
            "total_delivered": self.total_delivered,
            "unique_delivered": unique_delivered,
            "duplicate_deliveries": self.duplicate_deliveries,
            "delivery_ratio": round(delivery_ratio, 4),
        }