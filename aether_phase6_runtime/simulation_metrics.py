from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class SimulationRoutingMetric:
    """
    Deterministic record of a single routing decision at the simulation boundary.
    """

    routing_mode: str
    selected_next_hop: Optional[str]
    decision_reason: str
    candidate_count_before: int
    candidate_count_after: int
    phase6_filtered_all: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "simulation_routing_metric",
            "version": "1.0",
            "routing_mode": self.routing_mode,
            "selected_next_hop": self.selected_next_hop,
            "decision_reason": self.decision_reason,
            "candidate_count_before": self.candidate_count_before,
            "candidate_count_after": self.candidate_count_after,
            "phase6_filtered_all": self.phase6_filtered_all,
        }


@dataclass(frozen=True)
class SimulationRoutingMetricsSummary:
    """
    Aggregated simulation-level metrics for comparing routing mode impact.
    """

    total_decisions: int
    mode_counts: Dict[str, int]
    filtered_all_count: int
    selected_next_hop_counts: Dict[str, int]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "mode_counts",
            {key: self.mode_counts[key] for key in sorted(self.mode_counts.keys())},
        )
        object.__setattr__(
            self,
            "selected_next_hop_counts",
            {
                key: self.selected_next_hop_counts[key]
                for key in sorted(self.selected_next_hop_counts.keys())
            },
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "simulation_routing_metrics_summary",
            "version": "1.0",
            "total_decisions": self.total_decisions,
            "mode_counts": dict(self.mode_counts),
            "filtered_all_count": self.filtered_all_count,
            "selected_next_hop_counts": dict(self.selected_next_hop_counts),
        }


class SimulationRoutingMetricsCollector:
    """
    Observer utility to collect and aggregate simulation-level routing metrics.

    This collector does not mutate routing state.
    """

    def __init__(self) -> None:
        self._records: List[SimulationRoutingMetric] = []

    def record(self, metric: SimulationRoutingMetric) -> None:
        self._records.append(metric)

    def record_policy_decision(
        self,
        routing_mode: str,
        selected_next_hop: Optional[str],
        decision_reason: str,
        candidate_count_before: int,
        candidate_count_after: int,
    ) -> None:
        phase6_filtered_all = (
            candidate_count_before > 0 and candidate_count_after == 0
        )

        self.record(
            SimulationRoutingMetric(
                routing_mode=routing_mode,
                selected_next_hop=selected_next_hop,
                decision_reason=decision_reason,
                candidate_count_before=candidate_count_before,
                candidate_count_after=candidate_count_after,
                phase6_filtered_all=phase6_filtered_all,
            )
        )

    def summary(self) -> SimulationRoutingMetricsSummary:
        if not self._records:
            return SimulationRoutingMetricsSummary(
                total_decisions=0,
                mode_counts={},
                filtered_all_count=0,
                selected_next_hop_counts={},
            )

        mode_counts: Dict[str, int] = {}
        selected_next_hop_counts: Dict[str, int] = {}
        filtered_all_count = 0

        for record in self._records:
            mode_counts[record.routing_mode] = (
                mode_counts.get(record.routing_mode, 0) + 1
            )

            if record.phase6_filtered_all:
                filtered_all_count += 1

            hop_key = (
                record.selected_next_hop
                if record.selected_next_hop is not None
                else "NONE"
            )
            selected_next_hop_counts[hop_key] = (
                selected_next_hop_counts.get(hop_key, 0) + 1
            )

        return SimulationRoutingMetricsSummary(
            total_decisions=len(self._records),
            mode_counts=mode_counts,
            filtered_all_count=filtered_all_count,
            selected_next_hop_counts=selected_next_hop_counts,
        )

    def get_records(self) -> List[SimulationRoutingMetric]:
        return list(self._records)