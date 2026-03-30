from dataclasses import dataclass
from typing import Any, Dict

from aether_routing_scoring import RoutingScoreReport


@dataclass(frozen=True)
class EvaluationResult:
    """
    Deterministic result of evaluating a single case.
    """

    case_id: str
    scenario_name: str
    time_index: int
    routing_score_report: RoutingScoreReport
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a stable JSON-serializable representation of the evaluation result.
        """
        exported_metadata = {
            "scorer_name": self.metadata.get("scorer_name"),
            "scorer_version": self.metadata.get("scorer_version"),
            "candidate_link_count": self.metadata.get("candidate_link_count", 0),
        }

        return {
            "case_id": self.case_id,
            "scenario_name": self.scenario_name,
            "time_index": self.time_index,
            "metadata": exported_metadata,
            "routing_score_report": self.routing_score_report.to_dict(),
        }