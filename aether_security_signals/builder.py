from typing import Any, Dict, List

from aether_routing_context import RoutingContext
from aether_routing_scoring import RoutingScoreReport

from .link_signal import LinkSecuritySignal
from .node_signal import NodeSecuritySignal
from .report import SecuritySignalReport


class SecuritySignalBuilder:
    """
    Build a deterministic security-facing signal report from RoutingContext
    and RoutingScoreReport.
    """

    @staticmethod
    def _validate_context_and_score_report_alignment(
        context: RoutingContext,
        score_report: RoutingScoreReport,
    ) -> None:
        if context.scenario_name != score_report.scenario_name:
            raise ValueError(
                "RoutingContext and RoutingScoreReport scenario_name do not match"
            )
        if context.time_index != score_report.time_index:
            raise ValueError(
                "RoutingContext and RoutingScoreReport time_index do not match"
            )
        if context.source_node_id != score_report.source_node_id:
            raise ValueError(
                "RoutingContext and RoutingScoreReport source_node_id do not match"
            )
        if context.destination_node_id != score_report.destination_node_id:
            raise ValueError(
                "RoutingContext and RoutingScoreReport destination_node_id do not match"
            )

    @staticmethod
    def _validate_candidate_links(
        context: RoutingContext,
        score_report: RoutingScoreReport,
    ) -> None:
        candidate_links = set(context.candidate_link_ids)
        for link_score in score_report.link_scores:
            if link_score.link_id not in candidate_links:
                raise ValueError(
                    f"Link {link_score.link_id} in score report is not a valid candidate in the routing context"
                )

    @staticmethod
    def _build_link_signal(
        context: RoutingContext,
        link_id: str,
        estimated_success_probability: float,
    ) -> LinkSecuritySignal:
        observation = context.network_observation

        jammed = link_id in observation.jammed_links
        malicious_drop_risk = link_id in observation.malicious_drop_links
        degraded = link_id in observation.degraded_links
        extra_delay_ms = observation.extra_delay_ms_by_link.get(link_id, 0)
        injected_delay_ms = observation.injected_delay_ms_by_link.get(link_id, 0)

        reasons: List[str] = []

        if jammed or malicious_drop_risk or estimated_success_probability < 0.40:
            severity = "high"
            if jammed:
                reasons.append("jammed_link")
            if malicious_drop_risk:
                reasons.append("malicious_drop_risk")
            if estimated_success_probability < 0.40:
                reasons.append("estimated_success_probability<0.40")
        elif (
            degraded
            or extra_delay_ms > 0
            or injected_delay_ms > 0
            or estimated_success_probability < 0.75
        ):
            severity = "medium"
            if degraded:
                reasons.append("degraded_link")
            if extra_delay_ms > 0:
                reasons.append(f"extra_delay_ms={extra_delay_ms}")
            if injected_delay_ms > 0:
                reasons.append(f"injected_delay_ms={injected_delay_ms}")
            if estimated_success_probability < 0.75:
                reasons.append("estimated_success_probability<0.75")
        else:
            severity = "low"

        return LinkSecuritySignal(
            link_id=link_id,
            jammed=jammed,
            malicious_drop_risk=malicious_drop_risk,
            degraded=degraded,
            extra_delay_ms=extra_delay_ms,
            injected_delay_ms=injected_delay_ms,
            estimated_success_probability=estimated_success_probability,
            severity=severity,
            reasons=reasons,
        )

    @staticmethod
    def _build_node_signal(
        node_id: str,
        compromised_nodes: List[str],
    ) -> NodeSecuritySignal:
        compromised = node_id in compromised_nodes
        if compromised:
            return NodeSecuritySignal(
                node_id=node_id,
                compromised=True,
                severity="high",
                reasons=["compromised_node"],
            )
        return NodeSecuritySignal(
            node_id=node_id,
            compromised=False,
            severity="low",
            reasons=[],
        )

    @staticmethod
    def _build_summary(
        link_signals: List[LinkSecuritySignal],
        node_signals: List[NodeSecuritySignal],
    ) -> Dict[str, int]:
        return {
            "high_severity_link_count": sum(
                1 for signal in link_signals if signal.severity == "high"
            ),
            "medium_severity_link_count": sum(
                1 for signal in link_signals if signal.severity == "medium"
            ),
            "low_severity_link_count": sum(
                1 for signal in link_signals if signal.severity == "low"
            ),
            "compromised_node_count": sum(
                1 for signal in node_signals if signal.compromised
            ),
            "jammed_link_count": sum(
                1 for signal in link_signals if signal.jammed
            ),
            "malicious_drop_link_count": sum(
                1 for signal in link_signals if signal.malicious_drop_risk
            ),
        }

    def build(
        self,
        context: RoutingContext,
        score_report: RoutingScoreReport,
    ) -> SecuritySignalReport:
        self._validate_context_and_score_report_alignment(context, score_report)
        self._validate_candidate_links(context, score_report)

        link_signals = [
            self._build_link_signal(
                context=context,
                link_id=link_score.link_id,
                estimated_success_probability=link_score.estimated_success_probability,
            )
            for link_score in score_report.link_scores
        ]

        compromised_nodes = list(context.network_observation.compromised_nodes)
        node_signals = [
            self._build_node_signal(node_id, compromised_nodes)
            for node_id in context.network_observation.node_ids
        ]

        summary = self._build_summary(link_signals, node_signals)

        return SecuritySignalReport(
            scenario_name=context.scenario_name,
            time_index=context.time_index,
            source_node_id=context.source_node_id,
            destination_node_id=context.destination_node_id,
            link_signals=link_signals,
            node_signals=node_signals,
            summary=summary,
            metadata={
                "builder_name": "SecuritySignalBuilder",
                "builder_version": "1.0",
            },
        )