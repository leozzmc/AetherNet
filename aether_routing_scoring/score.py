from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class LinkScore:
    """
    Deterministic, explainable score for a single candidate link.

    This model is intentionally limited to scoring output only.
    It does not perform route selection or policy decisions.
    """

    link_id: str
    base_score: float
    penalties: Dict[str, float]
    total_penalty: float
    final_score: float
    estimated_success_probability: float
    reasons: List[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "penalties", dict(self.penalties))
        object.__setattr__(self, "reasons", list(self.reasons))

    @staticmethod
    def _sorted_penalties(data: Dict[str, float]) -> Dict[str, float]:
        return {key: data[key] for key in sorted(data.keys())}

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a stable, JSON-serializable representation.

        Penalties are exported in sorted-key order.
        Reasons are exported in sorted order for deterministic artifact stability.
        """
        return {
            "link_id": self.link_id,
            "base_score": self.base_score,
            "penalties": self._sorted_penalties(self.penalties),
            "total_penalty": self.total_penalty,
            "final_score": self.final_score,
            "estimated_success_probability": self.estimated_success_probability,
            "reasons": sorted(self.reasons),
        }