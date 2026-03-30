from dataclasses import dataclass
from typing import Any, Dict, List

from .decision import LinkDecision


@dataclass(frozen=True)
class SecurityAwareRoutingDecision:
    """
    Aggregate deterministic security-aware routing decision artifact.
    """

    scenario_name: str
    time_index: int
    source_node_id: str
    destination_node_id: str
    link_decisions: List[LinkDecision]
    recommended_link_ids: List[str]
    avoided_link_ids: List[str]
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "link_decisions", list(self.link_decisions))
        object.__setattr__(self, "recommended_link_ids", list(self.recommended_link_ids))
        object.__setattr__(self, "avoided_link_ids", list(self.avoided_link_ids))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        sorted_decisions = sorted(self.link_decisions, key=lambda decision: decision.link_id)

        exported_metadata = {
            "engine_name": self.metadata.get("engine_name"),
            "engine_version": self.metadata.get("engine_version"),
            "preferred_link_count": self.metadata.get("preferred_link_count", 0),
            "allowed_link_count": self.metadata.get("allowed_link_count", 0),
            "avoid_link_count": self.metadata.get("avoid_link_count", 0),
        }

        return {
            "type": "security_aware_routing_decision",
            "version": "1.0",
            "scenario_name": self.scenario_name,
            "time_index": self.time_index,
            "task": {
                "source_node_id": self.source_node_id,
                "destination_node_id": self.destination_node_id,
            },
            "recommendation": {
                "recommended_link_ids": sorted(self.recommended_link_ids),
                "avoided_link_ids": sorted(self.avoided_link_ids),
            },
            "metadata": exported_metadata,
            "link_decisions": [decision.to_dict() for decision in sorted_decisions],
        }