from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class LinkSecuritySignal:
    """
    Deterministic security-facing signal for a single link.
    """

    link_id: str
    jammed: bool
    malicious_drop_risk: bool
    degraded: bool
    extra_delay_ms: int
    injected_delay_ms: int
    estimated_success_probability: float
    severity: str
    reasons: List[str]

    def __post_init__(self) -> None:
        if self.severity not in {"low", "medium", "high"}:
            raise ValueError(
                f"LinkSecuritySignal severity must be one of low/medium/high, got {self.severity}"
            )
        object.__setattr__(self, "reasons", list(self.reasons))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "link_id": self.link_id,
            "jammed": self.jammed,
            "malicious_drop_risk": self.malicious_drop_risk,
            "degraded": self.degraded,
            "extra_delay_ms": self.extra_delay_ms,
            "injected_delay_ms": self.injected_delay_ms,
            "estimated_success_probability": self.estimated_success_probability,
            "severity": self.severity,
            "reasons": sorted(self.reasons),
        }