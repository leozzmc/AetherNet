from typing import List, Dict

from aether_routing_context import RoutingContext
from aether_routing_scoring import ProbabilisticScorer
from aether_security_signals import SecuritySignalBuilder
from aether_security_routing import SecurityAwareRoutingEngine


class Phase6DecisionAdapter:
    """
    Wave-90: Runtime Bridge (Optimized + Backward Compatible)
    """

    def __init__(self) -> None:
        self._scorer = ProbabilisticScorer()
        self._signal_builder = SecuritySignalBuilder()
        self._decision_engine = SecurityAwareRoutingEngine()

    def _compute_decision_map(
        self,
        context: RoutingContext,
    ) -> Dict[str, str]:
        score_report = self._scorer.score(context)
        signal_report = self._signal_builder.build(context, score_report)
        decision = self._decision_engine.build_decision(
            context,
            score_report,
            signal_report,
        )

        return {
            d.link_id: d.decision
            for d in decision.link_decisions
        }

    def apply_decision(
        self,
        context: RoutingContext,
        candidate_link_ids: List[str],
    ) -> List[str]:
        if not candidate_link_ids:
            return []

        decision_map = self._compute_decision_map(context)

        preferred = []
        allowed = []

        for link_id in candidate_link_ids:
            decision_type = decision_map.get(link_id, "allowed")

            if decision_type == "avoid":
                continue

            if decision_type == "preferred":
                preferred.append(link_id)
            else:
                allowed.append(link_id)

        return preferred + allowed

    # 🔥 BACKWARD COMPATIBILITY (VERY IMPORTANT)

    def filter_candidates(
        self,
        context: RoutingContext,
        candidate_link_ids: List[str],
    ) -> List[str]:
        """
        Legacy API support (Wave-89 tests)
        """
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
        Legacy API support (Wave-90 tests)
        """
        decision_map = self._compute_decision_map(context)

        preferred = []
        allowed = []

        for link_id in candidate_link_ids:
            decision_type = decision_map.get(link_id, "allowed")

            if decision_type == "avoid":
                continue

            if decision_type == "preferred":
                preferred.append(link_id)
            else:
                allowed.append(link_id)

        return preferred + allowed