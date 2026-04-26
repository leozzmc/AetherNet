#!/usr/bin/env python3
from pathlib import Path
import sys

try:
    import streamlit as st
except ImportError:
    print("Streamlit is not installed.")
    print("Install it with: pip install streamlit")
    raise SystemExit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from aether_phase6_runtime.benchmarks import (
    RuntimeBenchmarkRunner,
    default_runtime_benchmark_scenarios,
)
from aether_phase6_runtime.report import BenchmarkReportBuilder
from aether_phase6_runtime.insight import RoutingInsightGenerator


@st.cache_data
def run_benchmark_pipeline() -> dict:
    runner = RuntimeBenchmarkRunner()
    scenarios = default_runtime_benchmark_scenarios()
    suite = runner.run_suite("dashboard_run", scenarios)

    report = BenchmarkReportBuilder().build(suite)
    return report.structured


def render_summary(summary: dict) -> None:
    st.header("Global Summary")

    col1, col2 = st.columns(2)
    col1.metric("Total Decisions", summary["total_decisions"])
    col2.metric("Filtered-All Count", summary["filtered_all_count"])

    st.subheader("Mode Counts")
    st.table(
        [
            {"Routing Mode": mode, "Count": count}
            for mode, count in summary["mode_counts"].items()
        ]
    )


def render_scenario_viewer(scenarios: list[dict]) -> None:
    st.header("Scenario Viewer")

    scenario_ids = [scenario["scenario_id"] for scenario in scenarios]
    selected_id = st.selectbox("Select scenario", scenario_ids)

    selected = next(
        scenario for scenario in scenarios if scenario["scenario_id"] == selected_id
    )

    # --- Table (pure data, no logic) ---
    rows = []
    for result in selected["results"]:
        hop = result["selected_next_hop"] or "NONE"
        rows.append(
            {
                "Mode": result["routing_mode"].replace("phase6_", ""),
                "Selected Next Hop": hop,
                "Decision Reason": result["decision_reason"],
            }
        )

    st.subheader(f"Scenario: {selected_id}")
    st.table(rows)

    # --- Insight Layer ---
    st.subheader("🧠 System Insights")

    generator = RoutingInsightGenerator()
    insight = generator.generate(selected)

    # Observations (neutral)
    for obs in insight.observations:
        st.write(f"• {obs}")

    st.write("")

    # Conclusions (semantic rendering)
    for conc in insight.conclusions:
        lower = conc.lower()

        if "vulnerable" in lower or "unsafe" in lower:
            st.error(conc)
        elif "improve" in lower or "preserve" in lower or "robust" in lower:
            st.success(conc)
        else:
            st.info(conc)


def main() -> None:
    st.set_page_config(
        page_title="AetherNet Runtime Benchmark",
        page_icon="🛰️",
        layout="wide",
    )

    st.title("AetherNet Phase-6 Runtime Benchmark Dashboard")
    st.markdown(
        "Deterministic comparison of legacy, Phase-6 balanced, and Phase-6 adaptive routing modes."
    )

    structured_report = run_benchmark_pipeline()

    render_summary(structured_report["summary"])
    st.divider()
    render_scenario_viewer(structured_report["scenarios"])

    with st.expander("Raw structured artifact"):
        st.json(structured_report)


if __name__ == "__main__":
    main()