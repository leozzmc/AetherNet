from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from aether_scenarios import ScenarioSpec


@dataclass(frozen=True)
class BenchmarkCaseSpec:
    """
    Deterministic specification for a single benchmark case.
    """

    case_id: str
    description: str
    scenario_spec: ScenarioSpec
    source_node_id: str
    destination_node_id: str
    time_index: int
    candidate_link_ids: Optional[List[str]] = None
    tags: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must be a non-empty string")
        if not self.source_node_id.strip():
            raise ValueError("source_node_id must be a non-empty string")
        if not self.destination_node_id.strip():
            raise ValueError("destination_node_id must be a non-empty string")
        if self.time_index < 0:
            raise ValueError(f"time_index cannot be negative, got {self.time_index}")

        object.__setattr__(self, "tags", list(self.tags) if self.tags is not None else [])

        if self.candidate_link_ids is not None:
            object.__setattr__(
                self,
                "candidate_link_ids",
                list(self.candidate_link_ids),
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "description": self.description,
            "scenario_name": self.scenario_spec.scenario_name,
            "source_node_id": self.source_node_id,
            "destination_node_id": self.destination_node_id,
            "time_index": self.time_index,
            "candidate_link_ids": (
                sorted(self.candidate_link_ids)
                if self.candidate_link_ids is not None
                else None
            ),
            "tags": sorted(self.tags),
        }