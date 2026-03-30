from dataclasses import dataclass
from typing import Any, Dict, List

from .score import LinkScore


@dataclass(frozen=True)
class RoutingScoreReport:
    """
    Deterministic scoring report for a routing context.

    This report packages:
    - routing task identity
    - per-link score results
    - conservative context-level metadata
    """

    scenario_name: str
    time_index: int
    source_node_id: str
    destination_node_id: str
    link_scores: List[LinkScore]
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "link_scores", list(self.link_scores))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a stable, JSON-serializable score report.

        Link scores are exported sorted by link_id.
        Metadata is exported with a stable explicit schema.
        """
        sorted_scores = sorted(self.link_scores, key=lambda score: score.link_id)

        exported_metadata = {
            "scorer_name": self.metadata.get("scorer_name"),
            "scorer_version": self.metadata.get("scorer_version"),
            "compromised_node_count": self.metadata.get("compromised_node_count", 0),
            "compromised_nodes": sorted(
                list(self.metadata.get("compromised_nodes", []))
            ),
        }

        return {
            "type": "routing_score_report",
            "version": "1.0",
            "scenario_name": self.scenario_name,
            "time_index": self.time_index,
            "task": {
                "source_node_id": self.source_node_id,
                "destination_node_id": self.destination_node_id,
            },
            "metadata": exported_metadata,
            "link_scores": [score.to_dict() for score in sorted_scores],
        }