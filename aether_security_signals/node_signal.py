from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class NodeSecuritySignal:
    """
    Deterministic security-facing signal for a single node.
    """

    node_id: str
    compromised: bool
    severity: str
    reasons: List[str]

    def __post_init__(self) -> None:
        if self.severity not in {"low", "high"}:
            raise ValueError(
                f"NodeSecuritySignal severity must be one of low/high, got {self.severity}"
            )
        object.__setattr__(self, "reasons", list(self.reasons))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "compromised": self.compromised,
            "severity": self.severity,
            "reasons": sorted(self.reasons),
        }