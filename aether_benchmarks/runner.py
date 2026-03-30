from typing import Dict, List, Protocol

from aether_routing_context import RoutingContext, RoutingContextBuilder
from aether_routing_scoring import RoutingScoreReport
from aether_scenarios import ScenarioGenerator
from aether_security_routing import (
    SecurityAwareRoutingDecision,
    SecurityAwareRoutingEngine,
)
from aether_security_signals import SecuritySignalBuilder, SecuritySignalReport

from .case_result import BenchmarkCaseResult
from .case_spec import BenchmarkCaseSpec
from .pack import BenchmarkPack
from .pack_result import BenchmarkPackResult


class RoutingScorer(Protocol):
    def score(self, context: RoutingContext) -> RoutingScoreReport:
        ...


class SecuritySignalBuilderProtocol(Protocol):
    def build(
        self,
        context: RoutingContext,
        score_report: RoutingScoreReport,
    ) -> SecuritySignalReport:
        ...


class SecurityRoutingEngineProtocol(Protocol):
    def build_decision(
        self,
        context: RoutingContext,
        score_report: RoutingScoreReport,
        signal_report: SecuritySignalReport,
    ) -> SecurityAwareRoutingDecision:
        ...


class BenchmarkRunner:
    """
    Deterministic benchmark orchestration engine for the Phase-6 pipeline.
    """

    @staticmethod
    def _build_case_result(
        case: BenchmarkCaseSpec,
        scenario_name: str,
        routing_context,
        routing_score_report,
        security_signal_report,
        security_aware_routing_decision,
    ) -> BenchmarkCaseResult:
        return BenchmarkCaseResult(
            case_id=case.case_id,
            scenario_name=scenario_name,
            routing_context=routing_context,
            routing_score_report=routing_score_report,
            security_signal_report=security_signal_report,
            security_aware_routing_decision=security_aware_routing_decision,
            metadata={
                "description": case.description,
                "tags": sorted(case.tags),
                "candidate_link_count": len(routing_context.candidate_link_ids),
            },
        )

    @staticmethod
    def _run_case(
        case: BenchmarkCaseSpec,
        scenario_generator: ScenarioGenerator,
        context_builder: RoutingContextBuilder,
        scorer: RoutingScorer,
        signal_builder: SecuritySignalBuilderProtocol,
        decision_engine: SecurityRoutingEngineProtocol,
    ) -> BenchmarkCaseResult:
        scenario = scenario_generator.generate(case.scenario_spec)

        routing_context = context_builder.build(
            scenario=scenario,
            time_index=case.time_index,
            source_node_id=case.source_node_id,
            destination_node_id=case.destination_node_id,
            candidate_link_ids=case.candidate_link_ids,
        )

        routing_score_report = scorer.score(routing_context)
        security_signal_report = signal_builder.build(
            routing_context,
            routing_score_report,
        )
        security_aware_routing_decision = decision_engine.build_decision(
            routing_context,
            routing_score_report,
            security_signal_report,
        )

        return BenchmarkRunner._build_case_result(
            case=case,
            scenario_name=scenario.scenario_name,
            routing_context=routing_context,
            routing_score_report=routing_score_report,
            security_signal_report=security_signal_report,
            security_aware_routing_decision=security_aware_routing_decision,
        )

    @staticmethod
    def _build_summary(
        case_results: List[BenchmarkCaseResult],
    ) -> Dict[str, int]:
        preferred_link_total = 0
        allowed_link_total = 0
        avoid_link_total = 0
        high_severity_link_total = 0
        compromised_node_total = 0

        for result in case_results:
            decision = result.security_aware_routing_decision
            signal_report = result.security_signal_report

            preferred_link_total += sum(
                1 for item in decision.link_decisions if item.decision == "preferred"
            )
            allowed_link_total += sum(
                1 for item in decision.link_decisions if item.decision == "allowed"
            )
            avoid_link_total += sum(
                1 for item in decision.link_decisions if item.decision == "avoid"
            )

            high_severity_link_total += signal_report.summary.get(
                "high_severity_link_count",
                0,
            )
            compromised_node_total += signal_report.summary.get(
                "compromised_node_count",
                0,
            )

        return {
            "case_count": len(case_results),
            "preferred_link_total": preferred_link_total,
            "allowed_link_total": allowed_link_total,
            "avoid_link_total": avoid_link_total,
            "high_severity_link_total": high_severity_link_total,
            "compromised_node_total": compromised_node_total,
        }

    def run_pack(
        self,
        pack: BenchmarkPack,
        scenario_generator: ScenarioGenerator,
        context_builder: RoutingContextBuilder,
        scorer: RoutingScorer,
        signal_builder: SecuritySignalBuilderProtocol,
        decision_engine: SecurityRoutingEngineProtocol,
    ) -> BenchmarkPackResult:
        sorted_cases = sorted(pack.cases, key=lambda case: case.case_id)

        case_results = [
            self._run_case(
                case=case,
                scenario_generator=scenario_generator,
                context_builder=context_builder,
                scorer=scorer,
                signal_builder=signal_builder,
                decision_engine=decision_engine,
            )
            for case in sorted_cases
        ]

        return BenchmarkPackResult(
            pack_name=pack.pack_name,
            case_results=case_results,
            summary=self._build_summary(case_results),
            metadata={
                "runner_name": "BenchmarkRunner",
                "runner_version": "1.0",
            },
        )