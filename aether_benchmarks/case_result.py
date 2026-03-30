from dataclasses import dataclass
from typing import Any, Dict

from aether_routing_context import RoutingContext
from aether_routing_scoring import RoutingScoreReport
from aether_security_routing import SecurityAwareRoutingDecision
from aether_security_signals import SecuritySignalReport


@dataclass(frozen=True)
class BenchmarkCaseResult:
    """
    Consolidated deterministic result for a single benchmark case execution.
    """

    case_id: str
    scenario_name: str
    routing_context: RoutingContext
    routing_score_report: RoutingScoreReport
    security_signal_report: SecuritySignalReport
    security_aware_routing_decision: SecurityAwareRoutingDecision
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        exported_metadata = {
            "description": self.metadata.get("description"),
            "tags": sorted(list(self.metadata.get("tags", []))),
            "candidate_link_count": self.metadata.get("candidate_link_count", 0),
        }

        return {
            "case_id": self.case_id,
            "scenario_name": self.scenario_name,
            "metadata": exported_metadata,
            "routing_context": self.routing_context.to_dict(),
            "routing_score_report": self.routing_score_report.to_dict(),
            "security_signal_report": self.security_signal_report.to_dict(),
            "security_aware_routing_decision": (
                self.security_aware_routing_decision.to_dict()
            ),
        }