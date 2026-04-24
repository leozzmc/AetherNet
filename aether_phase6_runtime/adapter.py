from typing import List

from aether_routing_context import RoutingContext
from aether_routing_scoring import ProbabilisticScorer
from aether_security_signals import SecuritySignalBuilder
from aether_security_routing import SecurityAwareRoutingEngine


class Phase6DecisionAdapter:
    """
    Wave-89: Runtime Bridge for Phase-6.

    Filters candidate links using Phase-6 decision outputs.
    """

    def __init__(self) -> None:
        self._scorer = ProbabilisticScorer()
        self._signal_builder = SecuritySignalBuilder()
        self._decision_engine = SecurityAwareRoutingEngine()

    def filter_candidates(
        self,
        context: RoutingContext,
        candidate_link_ids: List[str],
    ) -> List[str]:
        """
        Apply Phase-6 decision to filter candidates.

        Removes links classified as "avoid".
        Preserves input ordering.
        """

        if not candidate_link_ids:
            return []

        # ⚠️ Phase-7 TODO: cache / reuse decision result per context
        score_report = self._scorer.score(context)
        signal_report = self._signal_builder.build(context, score_report)
        decision = self._decision_engine.build_decision(
            context,
            score_report,
            signal_report,
        )

        # 🔥 FIX: derive avoid set from link_decisions
        avoid_set = {
            d.link_id
            for d in decision.link_decisions
            if d.decision == "avoid"
        }

        # 🔥 IMPORTANT: only filter within current candidate set
        filtered = [
            link_id
            for link_id in candidate_link_ids
            if link_id not in avoid_set
        ]

        return filtered