from typing import Any, Dict, List

from aether_routing_context import RoutingContext

from .report import RoutingScoreReport
from .score import LinkScore


class ProbabilisticScorer:
    """
    Deterministic, explainable scoring engine over RoutingContext.

    Scope:
    - evaluate candidate links independently
    - apply a fixed penalty model
    - produce a stable scoring report

    Non-goals:
    - route selection
    - graph reasoning
    - routing module integration
    """

    PENALTY_DEGRADED = 0.15
    PENALTY_JAMMED = 0.35
    PENALTY_MALICIOUS_DROP = 0.40
    MAX_PENALTY_EXTRA_DELAY = 0.20
    MAX_PENALTY_INJECTED_DELAY = 0.25

    def _score_link(self, context: RoutingContext, link_id: str) -> LinkScore:
        observation = context.network_observation

        base_score = 1.0
        penalties: Dict[str, float] = {}
        reasons: List[str] = []

        if link_id in observation.degraded_links:
            penalties["degraded_link"] = self.PENALTY_DEGRADED
            reasons.append("degraded_link")

        if link_id in observation.extra_delay_ms_by_link:
            extra_delay_ms = observation.extra_delay_ms_by_link[link_id]
            penalties["extra_delay_penalty"] = min(
                extra_delay_ms / 1000.0,
                self.MAX_PENALTY_EXTRA_DELAY,
            )
            reasons.append(f"extra_delay_ms={extra_delay_ms}")

        if link_id in observation.jammed_links:
            penalties["jammed_link"] = self.PENALTY_JAMMED
            reasons.append("jammed_link")

        if link_id in observation.malicious_drop_links:
            penalties["malicious_drop_risk"] = self.PENALTY_MALICIOUS_DROP
            reasons.append("malicious_drop_risk")

        if link_id in observation.injected_delay_ms_by_link:
            injected_delay_ms = observation.injected_delay_ms_by_link[link_id]
            penalties["injected_delay_penalty"] = min(
                injected_delay_ms / 1000.0,
                self.MAX_PENALTY_INJECTED_DELAY,
            )
            reasons.append(f"injected_delay_ms={injected_delay_ms}")

        total_penalty = sum(penalties.values())
        final_score = max(0.0, min(1.0, base_score - total_penalty))

        return LinkScore(
            link_id=link_id,
            base_score=base_score,
            penalties=penalties,
            total_penalty=total_penalty,
            final_score=final_score,
            estimated_success_probability=final_score,
            reasons=reasons,
        )

    @staticmethod
    def _build_metadata(context: RoutingContext) -> Dict[str, Any]:
        compromised_nodes = sorted(context.network_observation.compromised_nodes)
        return {
            "scorer_name": "ProbabilisticScorer",
            "scorer_version": "1.0",
            "compromised_node_count": len(compromised_nodes),
            "compromised_nodes": compromised_nodes,
        }

    def score(self, context: RoutingContext) -> RoutingScoreReport:
        link_scores = [
            self._score_link(context, link_id)
            for link_id in context.candidate_link_ids
        ]

        return RoutingScoreReport(
            scenario_name=context.scenario_name,
            time_index=context.time_index,
            source_node_id=context.source_node_id,
            destination_node_id=context.destination_node_id,
            link_scores=link_scores,
            metadata=self._build_metadata(context),
        )