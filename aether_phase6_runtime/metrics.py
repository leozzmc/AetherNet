from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RoutingMetrics:
    """
    Immutable record of a single routing decision's Phase-6 impact.
    """

    total_candidates: int
    filtered_candidates: int
    chosen_link: Optional[str]
    chosen_decision_type: str


@dataclass(frozen=True)
class RoutingMetricsSummary:
    """
    Aggregated summary of Phase-6 routing impact.
    """

    total_decisions: int
    preferred_ratio: float
    allowed_ratio: float
    average_filtered: float


class RoutingMetricsCollector:
    """
    Lightweight metrics collector for Phase-6 runtime impact.

    This collector is observer-only. It must not mutate routing behavior.
    """

    def __init__(self) -> None:
        self._records: List[RoutingMetrics] = []

    def record(
        self,
        original_candidates: List[str],
        final_candidates: List[str],
        chosen_link: Optional[str],
        decision_map: Dict[str, str],
    ) -> None:
        total = len(original_candidates)
        filtered = max(0, total - len(final_candidates))

        if chosen_link is None:
            decision_type = "none"
        else:
            decision_type = decision_map.get(chosen_link, "allowed")

        self._records.append(
            RoutingMetrics(
                total_candidates=total,
                filtered_candidates=filtered,
                chosen_link=chosen_link,
                chosen_decision_type=decision_type,
            )
        )

    def summary(self) -> RoutingMetricsSummary:
        total_decisions = len(self._records)

        if total_decisions == 0:
            return RoutingMetricsSummary(
                total_decisions=0,
                preferred_ratio=0.0,
                allowed_ratio=0.0,
                average_filtered=0.0,
            )

        preferred_count = sum(
            1 for record in self._records if record.chosen_decision_type == "preferred"
        )
        allowed_count = sum(
            1 for record in self._records if record.chosen_decision_type == "allowed"
        )
        filtered_total = sum(record.filtered_candidates for record in self._records)

        return RoutingMetricsSummary(
            total_decisions=total_decisions,
            preferred_ratio=preferred_count / total_decisions,
            allowed_ratio=allowed_count / total_decisions,
            average_filtered=filtered_total / total_decisions,
        )

    def get_records(self) -> List[RoutingMetrics]:
        return list(self._records)