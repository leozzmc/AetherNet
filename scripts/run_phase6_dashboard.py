#!/usr/bin/env python3
from pathlib import Path
import sys
import time

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from aether_phase6_runtime.benchmarks import (
    RuntimeBenchmarkRunner,
    default_runtime_benchmark_scenarios,
)
from aether_phase6_runtime.report import BenchmarkReportBuilder
from aether_phase6_runtime.insight import RoutingInsightGenerator
from aether_phase6_runtime.narrative import RoutingNarrativeGenerator


MODE_ORDER = ["legacy", "phase6_balanced", "phase6_adaptive"]


@st.cache_data
def run_pipeline():
    runner = RuntimeBenchmarkRunner()
    scenarios = default_runtime_benchmark_scenarios()
    suite = runner.run_suite("dashboard_demo", scenarios)

    report = BenchmarkReportBuilder().build(suite)
    return report.structured


# ----------------------------
# UI Components
# ----------------------------

def render_summary(summary):
    st.title("🛰️ AetherNet Phase-6 Interactive Demo")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Decisions", summary["total_decisions"])
    col2.metric("Filtered-All", summary["filtered_all_count"])
    col3.metric("Modes Evaluated", len(summary["mode_counts"]))


def get_result_map(results):
    return {
        r["routing_mode"]: r["selected_next_hop"]
        for r in results
    }


# ----------------------------
# 🔥 Story Mode (Architecture Safe)
# ----------------------------

def render_story_mode(scenario):
    st.subheader("🎬 Story Mode")

    results = scenario["results"]
    result_map = get_result_map(results)

    legacy = result_map.get("legacy")
    balanced = result_map.get("phase6_balanced")
    adaptive = result_map.get("phase6_adaptive")

    scenario_id = scenario["scenario_id"]

    # Fetch backend intelligence (Do NOT hardcode logic in UI)
    insight = RoutingInsightGenerator().generate(scenario)
    narrative = RoutingNarrativeGenerator().generate(scenario, insight)

    st.write(f"### Scenario Context: `{scenario_id.upper()}`")

    # Step 1
    st.markdown("#### 🔎 Step 1: Network Condition")
    st.info(f"Running simulation under **{scenario_id}** environment constraints.")

    # Step 2
    st.markdown("#### 🔴 Step 2: Legacy Decision")
    st.write(f"Selected: **{legacy or 'NONE'}**")

    # Step 3
    st.markdown("#### 🟢 Step 3: Phase-6 Decision")
    st.write(f"Balanced selected: **{balanced or 'NONE'}**")
    st.write(f"Adaptive selected: **{adaptive or 'NONE'}**")

    # Step 4
    st.markdown("#### 🧠 Step 4: What Happened")
    if legacy != balanced or legacy != adaptive:
        st.warning(narrative.demo)
    else:
        st.success(narrative.demo)

    # Step 5
    st.markdown("#### 📊 Step 5: System Impact")
    for conc in insight.conclusions:
        if "vulnerable" in conc.lower() or "critical" in conc.lower():
            st.error(conc)
        else:
            st.success(conc)


# ----------------------------
# Table Mode
# ----------------------------

def render_table_mode(scenario):
    st.subheader("📊 Table View")

    results = sorted(
        scenario["results"],
        key=lambda r: MODE_ORDER.index(r["routing_mode"]) if r["routing_mode"] in MODE_ORDER else 99
    )

    rows = []
    for r in results:
        hop = r["selected_next_hop"] or "NONE"
        rows.append({
            "Mode": r["routing_mode"].replace("phase6_", ""),
            "Next Hop": hop,
            "Reason": r["decision_reason"],
        })

    st.table(rows)


# ----------------------------
# Comparison Mode
# ----------------------------

def render_comparison_mode(scenario):
    st.subheader("⚔️ Direct Comparison")

    result_map = get_result_map(scenario["results"])

    legacy = result_map.get("legacy", "NONE")
    balanced = result_map.get("phase6_balanced", "NONE")
    adaptive = result_map.get("phase6_adaptive", "NONE")

    col1, col2, col3 = st.columns(3)

    col1.markdown(f"**Legacy**\n\n🔴 `{legacy}`")
    col2.markdown(f"**Balanced**\n\n🟢 `{balanced}`")
    col3.markdown(f"**Adaptive**\n\n🟢 `{adaptive}`")

    if legacy != balanced:
        st.warning("⚠️ High Risk: Decision divergence detected. Phase-6 initiated defensive rerouting.")
    else:
        st.success("✔ System Consensus: All modes align on optimal path.")


# ----------------------------
# Insight + Narrative
# ----------------------------

def render_analysis(scenario):
    with st.expander("🔬 Deep Dive: System Analytics", expanded=False):
        insight = RoutingInsightGenerator().generate(scenario)
        narrative = RoutingNarrativeGenerator().generate(scenario, insight)

        st.markdown("**Core Observations**")
        for obs in insight.observations:
            st.write(f"• {obs}")

        st.markdown("---")
        st.markdown("**Interview Pitch**")
        st.info(narrative.interview)


# ----------------------------
# Play Demo
# ----------------------------

def render_play_demo(scenario):
    st.subheader("▶ Play Demo Execution")

    if st.button("Run Simulation Step-by-Step"):
        placeholder = st.empty()
        steps = [
            "Initializing Routing Context...",
            "Evaluating baseline metrics...",
            "Applying Phase-6 Threat Signals...",
            "Computing Divergence...",
            "Finalizing Next-Hop Selection ✅"
        ]
        for step in steps:
            placeholder.info(step)
            time.sleep(0.6)


# ----------------------------
# Main
# ----------------------------

def main():
    st.set_page_config(
        page_title="AetherNet Phase-6 Demo",
        page_icon="🛰️",
        layout="centered", # Centered looks better for storytelling
    )

    data = run_pipeline()
    render_summary(data["summary"])
    st.divider()

    scenarios = data["scenarios"]
    scenario_ids = [s["scenario_id"] for s in scenarios]

    # Use a cleaner horizontal radio for scenario selection
    selected_id = st.radio("Select Network Scenario:", scenario_ids, horizontal=True)
    scenario = next(s for s in scenarios if s["scenario_id"] == selected_id)
    
    st.divider()

    view_mode = st.selectbox(
        "Select Visualization Mode",
        ["Story Mode", "Comparison Mode", "Data Table"]
    )

    if view_mode == "Story Mode":
        render_story_mode(scenario)
    elif view_mode == "Data Table":
        render_table_mode(scenario)
    else:
        render_comparison_mode(scenario)

    st.divider()
    render_analysis(scenario)
    st.divider()
    render_play_demo(scenario)


if __name__ == "__main__":
    main()