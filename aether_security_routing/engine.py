from typing import Any, Dict, List

from aether_routing_context import RoutingContext
from aether_routing_scoring import RoutingScoreReport
from aether_security_signals import SecuritySignalReport

from .decision import LinkDecision
from .report import SecurityAwareRoutingDecision


class SecurityAwareRoutingEngine:
    """
    Deterministic security-aware routing decision engine.

    This engine does not perform graph routing or simulator integration.
    It only classifies candidate links into:
    - preferred
    - allowed
    - avoid
    """

    @staticmethod
    def _validate_alignment(
        context: RoutingContext,
        score_report: RoutingScoreReport,
        signal_report: SecuritySignalReport,
    ) -> None:
        if not (
            context.scenario_name
            == score_report.scenario_name
            == signal_report.scenario_name
        ):
            raise ValueError("Mismatched scenario_name across input artifacts")
        if not (
            context.time_index
            == score_report.time_index
            == signal_report.time_index
        ):
            raise ValueError("Mismatched time_index across input artifacts")
        if not (
            context.source_node_id
            == score_report.source_node_id
            == signal_report.source_node_id
        ):
            raise ValueError("Mismatched source_node_id across input artifacts")
        if not (
            context.destination_node_id
            == score_report.destination_node_id
            == signal_report.destination_node_id
        ):
            raise ValueError("Mismatched destination_node_id across input artifacts")

    @staticmethod
    def _validate_candidate_coverage(
        context: RoutingContext,
        score_report: RoutingScoreReport,
        signal_report: SecuritySignalReport,
    ) -> None:
        candidate_links = set(context.candidate_link_ids)
        scored_links = {score.link_id for score in score_report.link_scores}
        signaled_links = {signal.link_id for signal in signal_report.link_signals}

        for link_id in scored_links:
            if link_id not in candidate_links:
                raise ValueError(
                    f"Scored link {link_id} is not a valid candidate"
                )

        for link_id in signaled_links:
            if link_id not in candidate_links:
                raise ValueError(
                    f"Signaled link {link_id} is not a valid candidate"
                )

        missing_scored_links = candidate_links - scored_links
        if missing_scored_links:
            raise ValueError(
                f"Missing scored links for candidates: {sorted(missing_scored_links)}"
            )

        missing_signaled_links = candidate_links - signaled_links
        if missing_signaled_links:
            raise ValueError(
                f"Missing signaled links for candidates: {sorted(missing_signaled_links)}"
            )

    @staticmethod
    def _build_link_decision(
        signal,
    ) -> LinkDecision:
        reasons: List[str] = []

        if (
            signal.severity == "high"
            or signal.jammed
            or signal.malicious_drop_risk
            or signal.estimated_success_probability < 0.40
        ):
            decision = "avoid"
            if signal.severity == "high":
                reasons.append("severity=high")
            if signal.jammed:
                reasons.append("jammed_link")
            if signal.malicious_drop_risk:
                reasons.append("malicious_drop_risk")
            if signal.estimated_success_probability < 0.40:
                reasons.append("estimated_success_probability<0.40")

        elif (
            signal.severity == "low"
            and signal.estimated_success_probability >= 0.75
        ):
            decision = "preferred"
            reasons.append("severity=low")
            reasons.append("estimated_success_probability>=0.75")

        else:
            decision = "allowed"
            if signal.severity == "medium":
                reasons.append("severity=medium")
            if signal.estimated_success_probability < 0.75:
                reasons.append("estimated_success_probability<0.75")

        return LinkDecision(
            link_id=signal.link_id,
            decision=decision,
            severity=signal.severity,
            estimated_success_probability=signal.estimated_success_probability,
            reasons=reasons,
        )

    @staticmethod
    def _build_metadata(
        preferred_link_ids: List[str],
        allowed_link_ids: List[str],
        avoided_link_ids: List[str],
    ) -> Dict[str, Any]:
        return {
            "engine_name": "SecurityAwareRoutingEngine",
            "engine_version": "1.0",
            "preferred_link_count": len(preferred_link_ids),
            "allowed_link_count": len(allowed_link_ids),
            "avoid_link_count": len(avoided_link_ids),
        }

    def build_decision(
        self,
        context: RoutingContext,
        score_report: RoutingScoreReport,
        signal_report: SecuritySignalReport,
    ) -> SecurityAwareRoutingDecision:
        self._validate_alignment(context, score_report, signal_report)
        self._validate_candidate_coverage(context, score_report, signal_report)

        signal_by_link = {
            signal.link_id: signal for signal in signal_report.link_signals
        }

        link_decisions: List[LinkDecision] = []
        preferred_link_ids: List[str] = []
        allowed_link_ids: List[str] = []
        avoided_link_ids: List[str] = []

        for link_id in sorted(context.candidate_link_ids):
            decision = self._build_link_decision(signal_by_link[link_id])
            link_decisions.append(decision)

            if decision.decision == "preferred":
                preferred_link_ids.append(link_id)
            elif decision.decision == "allowed":
                allowed_link_ids.append(link_id)
            else:
                avoided_link_ids.append(link_id)

        recommended_link_ids = (
            preferred_link_ids if preferred_link_ids else allowed_link_ids
        )

        return SecurityAwareRoutingDecision(
            scenario_name=context.scenario_name,
            time_index=context.time_index,
            source_node_id=context.source_node_id,
            destination_node_id=context.destination_node_id,
            link_decisions=link_decisions,
            recommended_link_ids=recommended_link_ids,
            avoided_link_ids=avoided_link_ids,
            metadata=self._build_metadata(
                preferred_link_ids=preferred_link_ids,
                allowed_link_ids=allowed_link_ids,
                avoided_link_ids=avoided_link_ids,
            ),
        )