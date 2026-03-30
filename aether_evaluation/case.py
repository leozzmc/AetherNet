from dataclasses import dataclass
from typing import Any, Dict

from aether_routing_context import RoutingContext
from aether_scenarios import GeneratedScenario


@dataclass(frozen=True)
class EvaluationCase:
    """
    Deterministic container representing a single evaluation target.
    """

    case_id: str
    scenario: GeneratedScenario
    routing_context: RoutingContext

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must be a non-empty string")

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a stable lightweight representation of the evaluation case.

        This intentionally avoids exporting the full heavy scenario artifact.
        """
        return {
            "case_id": self.case_id,
            "scenario_name": self.scenario.scenario_name,
            "master_seed": self.scenario.master_seed,
            "time_index": self.routing_context.time_index,
            "source_node_id": self.routing_context.source_node_id,
            "destination_node_id": self.routing_context.destination_node_id,
            "candidate_link_ids": sorted(self.routing_context.candidate_link_ids),
        }