from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class LinkDecision:
    """
    Deterministic security-aware decision for a single candidate link.
    """

    link_id: str
    decision: str
    severity: str
    estimated_success_probability: float
    reasons: List[str]

    def __post_init__(self) -> None:
        if self.decision not in {"preferred", "allowed", "avoid"}:
            raise ValueError(
                "LinkDecision decision must be one of preferred/allowed/avoid"
            )
        if self.severity not in {"low", "medium", "high"}:
            raise ValueError(
                "LinkDecision severity must be one of low/medium/high"
            )
        object.__setattr__(self, "reasons", list(self.reasons))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_id": self.link_id,
            "decision": self.decision,
            "severity": self.severity,
            "estimated_success_probability": self.estimated_success_probability,
            "reasons": sorted(self.reasons),
        }