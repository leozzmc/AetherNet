from typing import List, Protocol, Tuple

from aether_routing_context import RoutingContext
from aether_routing_scoring import RoutingScoreReport

from .case import EvaluationCase
from .result import EvaluationResult
from .summary import EvaluationSummary


class RoutingScorer(Protocol):
    def score(self, context: RoutingContext) -> RoutingScoreReport:
        ...


class PolicyEvaluationEngine:
    """
    Deterministic evaluation engine over evaluation cases and scorer outputs.
    """

    @staticmethod
    def _build_empty_summary() -> EvaluationSummary:
        return EvaluationSummary(
            case_count=0,
            total_link_score_count=0,
            scorer_name="Unknown",
            scorer_version="Unknown",
            average_final_score=0.0,
            average_success_probability=0.0,
            min_final_score=0.0,
            max_final_score=0.0,
            compromised_node_case_count=0,
            metadata={
                "engine_name": "PolicyEvaluationEngine",
                "engine_version": "1.0",
            },
        )

    @staticmethod
    def _build_result(
        case: EvaluationCase,
        report: RoutingScoreReport,
    ) -> EvaluationResult:
        return EvaluationResult(
            case_id=case.case_id,
            scenario_name=case.scenario.scenario_name,
            time_index=case.routing_context.time_index,
            routing_score_report=report,
            metadata={
                "scorer_name": report.metadata.get("scorer_name", "Unknown"),
                "scorer_version": report.metadata.get("scorer_version", "Unknown"),
                "candidate_link_count": len(report.link_scores),
            },
        )

    @staticmethod
    def _aggregate_reports(
        results: List[EvaluationResult],
    ) -> EvaluationSummary:
        if not results:
            return PolicyEvaluationEngine._build_empty_summary()

        total_link_score_count = 0
        sum_final_score = 0.0
        sum_success_probability = 0.0
        min_final_score = float("inf")
        max_final_score = float("-inf")
        compromised_node_case_count = 0

        scorer_name = "Unknown"
        scorer_version = "Unknown"

        for result in results:
            report = result.routing_score_report

            if scorer_name == "Unknown":
                scorer_name = report.metadata.get("scorer_name", "Unknown")
                scorer_version = report.metadata.get("scorer_version", "Unknown")

            if report.metadata.get("compromised_node_count", 0) > 0:
                compromised_node_case_count += 1

            for link_score in report.link_scores:
                total_link_score_count += 1
                sum_final_score += link_score.final_score
                sum_success_probability += link_score.estimated_success_probability

                if link_score.final_score < min_final_score:
                    min_final_score = link_score.final_score
                if link_score.final_score > max_final_score:
                    max_final_score = link_score.final_score

        if total_link_score_count == 0:
            average_final_score = 0.0
            average_success_probability = 0.0
            min_score = 0.0
            max_score = 0.0
        else:
            average_final_score = sum_final_score / total_link_score_count
            average_success_probability = (
                sum_success_probability / total_link_score_count
            )
            min_score = min_final_score
            max_score = max_final_score

        return EvaluationSummary(
            case_count=len(results),
            total_link_score_count=total_link_score_count,
            scorer_name=scorer_name,
            scorer_version=scorer_version,
            average_final_score=average_final_score,
            average_success_probability=average_success_probability,
            min_final_score=min_score,
            max_final_score=max_score,
            compromised_node_case_count=compromised_node_case_count,
            metadata={
                "engine_name": "PolicyEvaluationEngine",
                "engine_version": "1.0",
            },
        )

    def evaluate_cases(
        self,
        cases: List[EvaluationCase],
        scorer: RoutingScorer,
    ) -> Tuple[List[EvaluationResult], EvaluationSummary]:
        sorted_cases = sorted(cases, key=lambda case: case.case_id)

        results: List[EvaluationResult] = []
        for case in sorted_cases:
            report = scorer.score(case.routing_context)
            results.append(self._build_result(case, report))

        summary = self._aggregate_reports(results)
        return results, summary