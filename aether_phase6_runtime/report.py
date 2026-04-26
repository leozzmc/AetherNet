import copy
from dataclasses import dataclass
from typing import Any, Dict, List

from .benchmarks import RuntimeBenchmarkResult, RuntimeBenchmarkSuiteResult


@dataclass(frozen=True)
class BenchmarkReport:
    """
    Deterministic presentation and export artifact for a benchmark suite run.
    """

    suite_id: str
    text: str
    structured: Dict[str, Any]

    def __post_init__(self) -> None:
        if not self.suite_id.strip():
            raise ValueError("suite_id must be a non-empty string")

        object.__setattr__(self, "structured", copy.deepcopy(self.structured))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "benchmark_report",
            "version": "1.0",
            "suite_id": self.suite_id,
            "text": self.text,
            "structured": copy.deepcopy(self.structured),
        }


class BenchmarkReportBuilder:
    """
    Converts RuntimeBenchmarkSuiteResult into:
    - deterministic human-readable text
    - UI-ready structured export
    """

    _MODE_ORDER = [
        "legacy",
        "phase6_balanced",
        "phase6_adaptive",
    ]

    def _mode_sort_key(self, result: RuntimeBenchmarkResult) -> tuple[int, str]:
        if result.routing_mode in self._MODE_ORDER:
            return (self._MODE_ORDER.index(result.routing_mode), result.routing_mode)
        return (len(self._MODE_ORDER), result.routing_mode)

    def _sort_results(
        self,
        results: List[RuntimeBenchmarkResult],
    ) -> List[RuntimeBenchmarkResult]:
        return sorted(results, key=self._mode_sort_key)

    @staticmethod
    def _display_mode(routing_mode: str) -> str:
        if routing_mode.startswith("phase6_"):
            return routing_mode.replace("phase6_", "", 1)
        return routing_mode

    @staticmethod
    def _display_hop(selected_next_hop: str | None) -> str:
        return selected_next_hop if selected_next_hop is not None else "NONE"

    def _group_by_scenario(
        self,
        results: List[RuntimeBenchmarkResult],
    ) -> Dict[str, List[RuntimeBenchmarkResult]]:
        grouped: Dict[str, List[RuntimeBenchmarkResult]] = {}

        for result in results:
            grouped.setdefault(result.scenario_id, []).append(result)

        return {
            scenario_id: grouped[scenario_id]
            for scenario_id in sorted(grouped.keys())
        }

    def build(
        self,
        suite_result: RuntimeBenchmarkSuiteResult,
    ) -> BenchmarkReport:
        grouped_results = self._group_by_scenario(suite_result.results)

        structured: Dict[str, Any] = {
            "suite_id": suite_result.suite_id,
            "summary": suite_result.summary.to_dict(),
            "scenarios": [],
        }

        for scenario_id, results in grouped_results.items():
            sorted_results = self._sort_results(results)
            structured["scenarios"].append(
                {
                    "scenario_id": scenario_id,
                    "results": [
                        {
                            "routing_mode": result.routing_mode,
                            "selected_next_hop": result.selected_next_hop,
                            "decision_reason": result.decision_reason,
                        }
                        for result in sorted_results
                    ],
                }
            )

        lines: List[str] = [
            "=== Phase-6 Runtime Benchmark Report ===",
            f"Suite: {suite_result.suite_id}",
            "",
            "[Summary]",
            f"Total Decisions: {suite_result.summary.total_decisions}",
            "",
            "Mode Counts:",
        ]

        for mode in self._MODE_ORDER:
            if mode in suite_result.summary.mode_counts:
                lines.append(f"- {mode}: {suite_result.summary.mode_counts[mode]}")

        for mode, count in sorted(suite_result.summary.mode_counts.items()):
            if mode not in self._MODE_ORDER:
                lines.append(f"- {mode}: {count}")

        lines.extend(
            [
                "",
                f"Filtered-All Count: {suite_result.summary.filtered_all_count}",
                "",
                "[Per Scenario]",
            ]
        )

        for scenario_id, results in grouped_results.items():
            lines.append("")
            lines.append(f"Scenario: {scenario_id}")

            for result in self._sort_results(results):
                lines.append(
                    f"- {self._display_mode(result.routing_mode)} "
                    f"-> {self._display_hop(result.selected_next_hop)}"
                )

        return BenchmarkReport(
            suite_id=suite_result.suite_id,
            text="\n".join(lines),
            structured=structured,
        )