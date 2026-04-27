#!/usr/bin/env python3
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

try:
    import streamlit as st
except ImportError:
    print("Streamlit is not installed.")
    print("Install it with: pip install streamlit")
    raise SystemExit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from aether_phase6_runtime.benchmarks import (  # noqa: E402
    RuntimeBenchmarkRunner,
    default_runtime_benchmark_scenarios,
)
from aether_phase6_runtime.insight import RoutingInsightGenerator  # noqa: E402
from aether_phase6_runtime.narrative import RoutingNarrativeGenerator  # noqa: E402
from aether_phase6_runtime.report import BenchmarkReportBuilder  # noqa: E402
from aether_phase6_runtime.trace import DecisionTraceBuilder  # noqa: E402


MODE_ORDER = ["legacy", "phase6_balanced", "phase6_adaptive"]


@st.cache_data
def run_pipeline() -> Dict[str, Any]:
    runner = RuntimeBenchmarkRunner()
    scenarios = default_runtime_benchmark_scenarios()
    suite = runner.run_suite("dashboard_demo", scenarios)

    report = BenchmarkReportBuilder().build(suite)
    return report.structured


def get_result_map(results: List[Dict[str, Any]]) -> Dict[str, str]:
    return {
        result["routing_mode"]: result["selected_next_hop"] or "NONE"
        for result in results
    }


def render_status_message(status: str, text: str) -> None:
    renderers = {
        "info": st.info,
        "success": st.success,
        "warning": st.warning,
        "error": st.error,
    }
    renderers.get(status, st.info)(text)


def render_placeholder_status(placeholder: Any, status: str, text: str) -> None:
    renderers = {
        "info": placeholder.info,
        "success": placeholder.success,
        "warning": placeholder.warning,
        "error": placeholder.error,
    }
    renderers.get(status, placeholder.info)(text)


def render_summary(summary: Dict[str, Any]) -> None:
    with st.container():
        st.title("🛰️ AetherNet Phase-6 Product Demo")
        st.markdown(
            "Deterministic comparison of legacy baseline vs. Phase-6 active security routing modes."
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Decisions Executed", summary["total_decisions"])
        col2.metric("Extreme Lockdowns", summary["filtered_all_count"])
        col3.metric("Routing Modes", len(summary["mode_counts"]))

        st.divider()


def render_trace_pipeline(trace: Any) -> None:
    st.markdown("### 🧪 Routing Pipeline Trace")

    pipeline = " → ".join(step.text for step in trace.steps)
    st.code(pipeline)

    for step in trace.steps:
        render_status_message(step.status, step.text)


def render_story_mode(
    scenario: Dict[str, Any],
    insight: Any,
    narrative: Any,
    trace: Any,
) -> None:
    st.subheader("🎬 Story Mode")

    result_map = get_result_map(scenario["results"])
    legacy = result_map.get("legacy", "NONE")
    balanced = result_map.get("phase6_balanced", "NONE")
    adaptive = result_map.get("phase6_adaptive", "NONE")

    scenario_id = scenario["scenario_id"]

    with st.container():
        st.markdown("### 🔎 Context")
        st.info(
            f"Running deterministic simulation for scenario constraint: "
            f"**`{scenario_id.upper()}`**"
        )

    with st.container():
        render_trace_pipeline(trace)

    st.divider()

    with st.container():
        st.markdown("### ⚖️ Decision Difference")
        col1, col2 = st.columns(2)

        if legacy == balanced:
            with col1:
                st.info(f"**Legacy Routing Selected:**\n\n### {legacy}")
            with col2:
                st.info(f"**Phase-6 Routing Selected:**\n\n### {balanced}")
        else:
            with col1:
                st.error(f"**Legacy Routing Selected:**\n\n### {legacy}")
            with col2:
                st.success(f"**Phase-6 Routing Selected:**\n\n### {balanced}")

        if adaptive != balanced:
            st.caption(f"Adaptive mode selected: `{adaptive}`")

    with st.container():
        st.markdown("### 🧠 System Behavior")
        render_status_message(narrative.demo_status, narrative.demo)

    with st.container():
        st.markdown("### 📊 Impact")
        for conclusion in insight.conclusions:
            render_status_message(conclusion.status, conclusion.text)


def render_comparison_mode(scenario: Dict[str, Any]) -> None:
    st.subheader("⚔️ Direct Comparison")

    result_map = get_result_map(scenario["results"])
    legacy = result_map.get("legacy", "NONE")
    balanced = result_map.get("phase6_balanced", "NONE")
    adaptive = result_map.get("phase6_adaptive", "NONE")

    col1, col2, col3 = st.columns(3)
    col1.metric("Legacy Baseline", legacy)
    col2.metric("Phase-6 Balanced", balanced)
    col3.metric("Phase-6 Adaptive", adaptive)

    st.caption("Routing behavior comparison across modes.")


def render_table_mode(scenario: Dict[str, Any]) -> None:
    st.subheader("📊 Raw Data Table")

    sorted_results = sorted(
        scenario["results"],
        key=lambda result: (
            MODE_ORDER.index(result["routing_mode"])
            if result["routing_mode"] in MODE_ORDER
            else 99
        ),
    )

    rows = [
        {
            "Mode": result["routing_mode"].replace("phase6_", ""),
            "Selected Next Hop": result["selected_next_hop"] or "NONE",
            "Decision Reason": result["decision_reason"],
        }
        for result in sorted_results
    ]

    st.table(rows)


def render_play_demo(trace: Any, narrative: Any) -> None:
    st.subheader("▶ Live Simulation Reel")

    if st.button("▶ Run Simulation Step-by-Step"):
        placeholder = st.empty()

        for step in trace.steps:
            render_placeholder_status(placeholder, step.status, step.text)
            time.sleep(0.8)

        placeholder.success("Simulation complete.")
        time.sleep(0.5)
        placeholder.markdown(f"> **Conclusion:** {narrative.summary}")


def render_analysis(insight: Any, narrative: Any) -> None:
    with st.expander("🔬 Deep Dive Analysis", expanded=False):
        st.markdown("**Core Backend Observations**")
        for observation in insight.observations:
            st.write(f"• {observation}")

        st.markdown("---")
        st.markdown("**Core Backend Conclusions**")
        for conclusion in insight.conclusions:
            render_status_message(conclusion.status, conclusion.text)

        st.markdown("---")
        st.markdown("**Technical Context**")
        render_status_message(narrative.summary_status, narrative.interview)


def main() -> None:
    st.set_page_config(
        page_title="AetherNet Product Demo",
        page_icon="🛰️",
        layout="centered",
    )

    data = run_pipeline()

    render_summary(data["summary"])

    scenarios = data["scenarios"]
    scenario_ids = [scenario["scenario_id"] for scenario in scenarios]

    with st.container():
        st.markdown("### 1. Select Network Scenario Constraint")
        selected_id = st.radio(
            "Scenario",
            scenario_ids,
            horizontal=True,
            label_visibility="collapsed",
        )
        scenario = next(item for item in scenarios if item["scenario_id"] == selected_id)

        insight = RoutingInsightGenerator().generate(scenario)
        narrative = RoutingNarrativeGenerator().generate(scenario, insight)
        trace = DecisionTraceBuilder().build(scenario)

    st.divider()

    with st.container():
        st.markdown("### 2. Visualization")
        view_mode = st.radio(
            "Select View Mode",
            ["Story Mode", "Comparison Mode", "Table View"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if view_mode == "Story Mode":
            render_story_mode(scenario, insight, narrative, trace)
        elif view_mode == "Comparison Mode":
            render_comparison_mode(scenario)
        else:
            render_table_mode(scenario)

    st.divider()

    with st.container():
        st.markdown("### 3. Dynamic Execution")
        render_play_demo(trace, narrative)

    st.divider()

    render_analysis(insight, narrative)

    with st.expander("🛠️ Inspect Raw Deterministic Artifact"):
        st.json(data)


if __name__ == "__main__":
    main()