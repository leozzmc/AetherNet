from typing import Dict, List, Tuple

from aether_routing_context import RoutingContext
from aether_routing_scoring import ProbabilisticScorer
from aether_security_routing import SecurityAwareRoutingEngine
from aether_security_signals import SecuritySignalBuilder


class Phase6DecisionAdapter:
    """
    Runtime bridge for Phase-6 decisions.

    The adapter computes the Phase-6 decision once, then reuses the result for:
    - filtering avoid links
    - prioritizing preferred links
    - exposing decision metadata for metrics
    """

    def __init__(self) -> None:
        self._scorer = ProbabilisticScorer()
        self._signal_builder = SecuritySignalBuilder()
        self._decision_engine = SecurityAwareRoutingEngine()

    def _compute_decision_map(self, context: RoutingContext) -> Dict[str, str]:
        score_report = self._scorer.score(context)
        signal_report = self._signal_builder.build(context, score_report)
        decision = self._decision_engine.build_decision(
            context,
            score_report,
            signal_report,
        )

        return {
            link_decision.link_id: link_decision.decision
            for link_decision in decision.link_decisions
        }

    def compute(
        self,
        context: RoutingContext,
        candidate_link_ids: List[str],
    ) -> Tuple[List[str], Dict[str, str]]:
        """
        Single-pass Phase-6 runtime decision.

        Returns:
        - filtered and prioritized candidate link IDs
        - decision_map: link_id -> preferred/allowed/avoid
        """

        if not candidate_link_ids:
            return [], {}

        decision_map = self._compute_decision_map(context)

        preferred: List[str] = []
        allowed: List[str] = []

        for link_id in candidate_link_ids:
            decision_type = decision_map.get(link_id, "allowed")

            if decision_type == "avoid":
                continue

            if decision_type == "preferred":
                preferred.append(link_id)
            else:
                allowed.append(link_id)

        return preferred + allowed, decision_map

    def get_decision_map(self, context: RoutingContext) -> Dict[str, str]:
        """
        Backward-compatible decision-map accessor.
        Prefer compute(...) in runtime paths to avoid recomputing the pipeline.
        """
        return self._compute_decision_map(context)

    def apply_decision(
        self,
        context: RoutingContext,
        candidate_link_ids: List[str],
    ) -> List[str]:
        candidates, _ = self.compute(context, candidate_link_ids)
        return candidates

    def filter_candidates(
        self,
        context: RoutingContext,
        candidate_link_ids: List[str],
    ) -> List[str]:
        """
        Backward-compatible Wave-89 API.

        Removes only avoid links and preserves original order.
        """

        if not candidate_link_ids:
            return []

        decision_map = self._compute_decision_map(context)

        return [
            link_id
            for link_id in candidate_link_ids
            if decision_map.get(link_id, "allowed") != "avoid"
        ]

    def prioritize_candidates(
        self,
        context: RoutingContext,
        candidate_link_ids: List[str],
    ) -> List[str]:
        """
        Backward-compatible Wave-90 API.

        Applies preferred-first grouping and removes avoid links.
        """

        candidates, _ = self.compute(context, candidate_link_ids)
        return candidates