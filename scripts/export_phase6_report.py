#!/usr/bin/env python3
from pathlib import Path
import sys
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from aether_phase6_runtime.benchmarks import (  # noqa: E402
    RuntimeBenchmarkRunner,
    default_runtime_benchmark_scenarios,
)
from aether_phase6_runtime.insight import RoutingInsightGenerator  # noqa: E402
from aether_phase6_runtime.narrative import RoutingNarrativeGenerator  # noqa: E402
from aether_phase6_runtime.report import BenchmarkReportBuilder  # noqa: E402


MODE_ORDER = ["legacy", "phase6_balanced", "phase6_adaptive"]


def _display_mode(mode: str) -> str:
    return mode.replace("phase6_", "", 1) if mode.startswith("phase6_") else mode


def _display_hop(hop: str | None) -> str:
    return hop if hop is not None else "NONE (Blocked)"


def _mode_sort_key(result: Dict[str, Any]) -> tuple[int, str]:
    mode = result["routing_mode"]
    if mode in MODE_ORDER:
        return (MODE_ORDER.index(mode), mode)
    return (len(MODE_ORDER), mode)


def _append_mode_counts(lines: List[str], mode_counts: Dict[str, int]) -> None:
    for mode in MODE_ORDER:
        if mode in mode_counts:
            lines.append(f"- `{_display_mode(mode)}`: {mode_counts[mode]} executions")

    for mode in sorted(mode_counts.keys()):
        if mode not in MODE_ORDER:
            lines.append(f"- `{_display_mode(mode)}`: {mode_counts[mode]} executions")


def _icon_for_conclusion(conclusion: str) -> str:
    """
    Lightweight presentation heuristic only.

    This is intentionally not system logic. The underlying system semantics
    live in the benchmark, insight, and narrative layers.
    """
    lower = conclusion.lower()

    if "vulnerable" in lower or "critical" in lower or "unsafe" in lower:
        return "🚨"

    if "improve" in lower or "preserve" in lower or "robust" in lower:
        return "✅"

    return "ℹ️"


def build_markdown(structured_data: Dict[str, Any]) -> str:
    lines: List[str] = []

    lines.append("# AetherNet Phase-6 Runtime Benchmark Report")
    lines.append("")
    lines.append("> Auto-generated deterministic evaluation artifact.")
    lines.append(f"> Suite ID: `{structured_data['suite_id']}`")
    lines.append("")

    summary = structured_data["summary"]

    lines.append("## Global Summary")
    lines.append("")
    lines.append(f"- **Total Decisions Simulated**: {summary['total_decisions']}")
    lines.append(
        f"- **Extreme Lockdown Events (Filtered-All)**: {summary['filtered_all_count']}"
    )
    lines.append("")
    lines.append("### Evaluated Routing Modes")
    _append_mode_counts(lines, summary["mode_counts"])
    lines.append("")
    lines.append("---")
    lines.append("")

    insight_generator = RoutingInsightGenerator()
    narrative_generator = RoutingNarrativeGenerator()

    for scenario in structured_data["scenarios"]:
        scenario_id = scenario["scenario_id"]

        lines.append(f"## Scenario: {scenario_id}")
        lines.append("")

        lines.append("### Routing Decisions")
        lines.append("")
        lines.append("| Routing Mode | Selected Next Hop | Decision Reason |")
        lines.append("|---|---|---|")

        sorted_results = sorted(scenario["results"], key=_mode_sort_key)

        for result in sorted_results:
            display_mode = _display_mode(result["routing_mode"])
            hop = _display_hop(result["selected_next_hop"])
            reason = result["decision_reason"]
            lines.append(f"| `{display_mode}` | **{hop}** | `{reason}` |")

        lines.append("")

        insight = insight_generator.generate(scenario)

        lines.append("### System Insights")
        lines.append("")
        lines.append("**Observations:**")
        for observation in insight.observations:
            lines.append(f"- {observation}")

        lines.append("")
        lines.append("**Conclusions:**")
        for conclusion in insight.conclusions:
            lines.append(f"- {_icon_for_conclusion(conclusion)} {conclusion}")

        lines.append("")

        narrative = narrative_generator.generate(scenario, insight)

        lines.append("### Explanatory Narrative")
        lines.append("")
        lines.append(f"> **Summary:** {narrative.summary}")
        lines.append("")
        lines.append("**Technical Context:**")
        lines.append("")
        lines.append(narrative.interview)
        lines.append("")
        lines.append("**Demo Script:**")
        lines.append("")
        lines.append(f"_{narrative.demo}_")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    runner = RuntimeBenchmarkRunner()
    scenarios = default_runtime_benchmark_scenarios()
    suite = runner.run_suite("export_cli", scenarios)

    report = BenchmarkReportBuilder().build(suite)
    markdown_output = build_markdown(report.structured)

    print(markdown_output)


if __name__ == "__main__":
    main()