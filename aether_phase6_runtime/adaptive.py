from typing import List, Optional

from aether_routing_context import RoutingContext

from .adapter import Phase6DecisionAdapter
from .metrics import RoutingMetricsSummary


class AdaptiveRuntimeMode:
    """
    Deterministic runtime modes for Phase-6 adaptive behavior.
    """

    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"

    ALL = {
        CONSERVATIVE,
        BALANCED,
        AGGRESSIVE,
    }


class AdaptiveRuntimePolicy:
    """
    Deterministic rule-based adaptive policy.

    This is intentionally not ML/RL. It maps recent routing metrics to a
    runtime mode using fixed thresholds.
    """

    @staticmethod
    def select_mode(summary: RoutingMetricsSummary) -> str:
        if summary.average_filtered >= 2.0:
            return AdaptiveRuntimeMode.CONSERVATIVE

        if summary.preferred_ratio >= 0.70:
            return AdaptiveRuntimeMode.AGGRESSIVE

        return AdaptiveRuntimeMode.BALANCED


class AdaptivePhase6Adapter:
    """
    Adaptive wrapper around Phase6DecisionAdapter.

    Modes:
    - conservative: keep preferred links only if any exist; otherwise allowed fallback
    - balanced: preferred first, then allowed
    - aggressive: preserve original order among all safe links to maximize routing freedom

    In every mode, avoid links are never returned.
    """

    def __init__(
        self,
        base_adapter: Optional[Phase6DecisionAdapter] = None,
        policy: Optional[AdaptiveRuntimePolicy] = None,
    ) -> None:
        self._base_adapter = base_adapter if base_adapter is not None else Phase6DecisionAdapter()
        self._policy = policy if policy is not None else AdaptiveRuntimePolicy()

    def apply_adaptive_decision(
        self,
        context: RoutingContext,
        candidate_link_ids: List[str],
        metrics_summary: RoutingMetricsSummary,
    ) -> List[str]:
        if not candidate_link_ids:
            return []

        safe_candidates, decision_map = self._base_adapter.compute(
            context,
            candidate_link_ids,
        )

        if not safe_candidates:
            return []

        mode = self._policy.select_mode(metrics_summary)

        if mode == AdaptiveRuntimeMode.CONSERVATIVE:
            return self._apply_conservative(safe_candidates, decision_map)

        if mode == AdaptiveRuntimeMode.BALANCED:
            return self._apply_balanced(safe_candidates, decision_map)

        if mode == AdaptiveRuntimeMode.AGGRESSIVE:
            return self._apply_aggressive(candidate_link_ids, decision_map)

        return self._apply_balanced(safe_candidates, decision_map)

    @staticmethod
    def _apply_conservative(
        safe_candidates: List[str],
        decision_map: dict[str, str],
    ) -> List[str]:
        preferred = [
            link_id
            for link_id in safe_candidates
            if decision_map.get(link_id, "allowed") == "preferred"
        ]

        if preferred:
            return preferred

        return [
            link_id
            for link_id in safe_candidates
            if decision_map.get(link_id, "allowed") != "avoid"
        ]

    @staticmethod
    def _apply_balanced(
        safe_candidates: List[str],
        decision_map: dict[str, str],
    ) -> List[str]:
        preferred: List[str] = []
        allowed: List[str] = []

        for link_id in safe_candidates:
            decision_type = decision_map.get(link_id, "allowed")

            if decision_type == "avoid":
                continue

            if decision_type == "preferred":
                preferred.append(link_id)
            else:
                allowed.append(link_id)

        return preferred + allowed

    @staticmethod
    def _apply_aggressive(
        original_candidates: List[str],
        decision_map: dict[str, str],
    ) -> List[str]:
        """
        Aggressive mode still removes avoid links, but preserves original route order
        among all safe candidates instead of hoisting preferred links.
        """
        return [
            link_id
            for link_id in original_candidates
            if decision_map.get(link_id, "allowed") != "avoid"
        ]