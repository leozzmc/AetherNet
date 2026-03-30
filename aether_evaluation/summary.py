from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class EvaluationSummary:
    """
    Deterministic aggregate summary across multiple evaluation cases.
    """

    case_count: int
    total_link_score_count: int
    scorer_name: str
    scorer_version: str
    average_final_score: float
    average_success_probability: float
    min_final_score: float
    max_final_score: float
    compromised_node_case_count: int
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a stable JSON-serializable representation of the aggregate summary.
        """
        exported_metadata = {
            "engine_name": self.metadata.get("engine_name"),
            "engine_version": self.metadata.get("engine_version"),
        }

        return {
            "type": "evaluation_summary",
            "version": "1.0",
            "scorer": {
                "scorer_name": self.scorer_name,
                "scorer_version": self.scorer_version,
            },
            "metrics": {
                "case_count": self.case_count,
                "total_link_score_count": self.total_link_score_count,
                "compromised_node_case_count": self.compromised_node_case_count,
                "average_final_score": self.average_final_score,
                "average_success_probability": self.average_success_probability,
                "min_final_score": self.min_final_score,
                "max_final_score": self.max_final_score,
            },
            "metadata": exported_metadata,
        }