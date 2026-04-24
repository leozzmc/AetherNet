from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from aether_routing_context import RoutingContext

from .adapter import Phase6DecisionAdapter
from .adaptive import AdaptivePhase6Adapter
from .metrics import RoutingMetricsSummary


CONSERVATIVE_SUMMARY = RoutingMetricsSummary(
    total_decisions=100,
    preferred_ratio=0.5,
    allowed_ratio=0.5,
    average_filtered=2.5,
)

BALANCED_SUMMARY = RoutingMetricsSummary(
    total_decisions=100,
    preferred_ratio=0.5,
    allowed_ratio=0.5,
    average_filtered=1.0,
)

AGGRESSIVE_SUMMARY = RoutingMetricsSummary(
    total_decisions=100,
    preferred_ratio=0.9,
    allowed_ratio=0.1,
    average_filtered=0.0,
)


@dataclass(frozen=True)
class PolicyComparisonCase:
    """
    Deterministic input container for one Phase-6 runtime policy comparison.
    """

    case_id: str
    context: RoutingContext
    candidate_link_ids: List[str]
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must be a non-empty string")

        object.__setattr__(self, "candidate_link_ids", list(self.candidate_link_ids))
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata) if self.metadata is not None else {},
        )


@dataclass(frozen=True)
class PolicyComparisonResult:
    """
    Stable comparison artifact for Phase-6 runtime policy outputs.
    """

    case_id: str
    baseline_candidates: List[str]
    conservative_candidates: List[str]
    balanced_candidates: List[str]
    aggressive_candidates: List[str]
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "baseline_candidates", list(self.baseline_candidates))
        object.__setattr__(
            self,
            "conservative_candidates",
            list(self.conservative_candidates),
        )
        object.__setattr__(self, "balanced_candidates", list(self.balanced_candidates))
        object.__setattr__(self, "aggressive_candidates", list(self.aggressive_candidates))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        exported_metadata = {
            "runner_name": self.metadata.get("runner_name", "PolicyComparisonRunner"),
            "runner_version": self.metadata.get("runner_version", "1.0"),
            "baseline_count": self.metadata.get("baseline_count", 0),
            "conservative_count": self.metadata.get("conservative_count", 0),
            "balanced_count": self.metadata.get("balanced_count", 0),
            "aggressive_count": self.metadata.get("aggressive_count", 0),
        }

        return {
            "type": "phase6_policy_comparison_result",
            "version": "1.0",
            "case_id": self.case_id,
            "baseline_candidates": list(self.baseline_candidates),
            "conservative_candidates": list(self.conservative_candidates),
            "balanced_candidates": list(self.balanced_candidates),
            "aggressive_candidates": list(self.aggressive_candidates),
            "metadata": exported_metadata,
        }


class PolicyComparisonRunner:
    """
    Deterministic automation layer for comparing Phase-6 runtime policy outputs.

    This runner does not introduce a new routing policy. It executes existing
    public adapter APIs against fixed mode-triggering summaries.
    """

    def __init__(
        self,
        base_adapter: Optional[Phase6DecisionAdapter] = None,
        adaptive_adapter: Optional[AdaptivePhase6Adapter] = None,
    ) -> None:
        self._base_adapter = base_adapter if base_adapter is not None else Phase6DecisionAdapter()
        self._adaptive_adapter = (
            adaptive_adapter
            if adaptive_adapter is not None
            else AdaptivePhase6Adapter(base_adapter=self._base_adapter)
        )

    def run_case(self, case: PolicyComparisonCase) -> PolicyComparisonResult:
        baseline = self._base_adapter.apply_decision(
            context=case.context,
            candidate_link_ids=case.candidate_link_ids,
        )

        conservative = self._adaptive_adapter.apply_adaptive_decision(
            context=case.context,
            candidate_link_ids=case.candidate_link_ids,
            metrics_summary=CONSERVATIVE_SUMMARY,
        )

        balanced = self._adaptive_adapter.apply_adaptive_decision(
            context=case.context,
            candidate_link_ids=case.candidate_link_ids,
            metrics_summary=BALANCED_SUMMARY,
        )

        aggressive = self._adaptive_adapter.apply_adaptive_decision(
            context=case.context,
            candidate_link_ids=case.candidate_link_ids,
            metrics_summary=AGGRESSIVE_SUMMARY,
        )

        metadata: Dict[str, Any] = {
            "runner_name": "PolicyComparisonRunner",
            "runner_version": "1.0",
            "baseline_count": len(baseline),
            "conservative_count": len(conservative),
            "balanced_count": len(balanced),
            "aggressive_count": len(aggressive),
        }

        return PolicyComparisonResult(
            case_id=case.case_id,
            baseline_candidates=baseline,
            conservative_candidates=conservative,
            balanced_candidates=balanced,
            aggressive_candidates=aggressive,
            metadata=metadata,
        )