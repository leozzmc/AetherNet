from dataclasses import dataclass
from typing import Any, Dict, List

from .observation import NetworkObservation


@dataclass(frozen=True)
class RoutingContext:
    """
    Deterministic routing decision input package.

    This object does not perform routing logic.
    It packages:
    - scenario identity
    - routing task parameters
    - candidate link universe
    - a NetworkObservation snapshot
    - stable metadata
    """

    scenario_name: str
    master_seed: int
    time_index: int
    source_node_id: str
    destination_node_id: str
    candidate_link_ids: List[str]
    network_observation: NetworkObservation
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "candidate_link_ids", list(self.candidate_link_ids))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a stable, JSON-serializable representation of the routing context.
        """
        return {
            "type": "routing_context",
            "version": "1.0",
            "scenario_name": self.scenario_name,
            "master_seed": self.master_seed,
            "time_index": self.time_index,
            "task": {
                "source_node_id": self.source_node_id,
                "destination_node_id": self.destination_node_id,
                "candidate_link_count": len(self.candidate_link_ids),
                "candidate_link_ids": sorted(self.candidate_link_ids),
            },
            "metadata": dict(self.metadata),
            "network_observation": self.network_observation.to_dict(),
        }