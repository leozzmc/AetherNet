#!/usr/bin/env python3
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from aether_phase6_runtime.comparison import (  # noqa: E402
    PolicyComparisonCase,
    PolicyComparisonRunner,
)
from aether_phase6_runtime.showcase import PolicyShowcaseBuilder  # noqa: E402
from aether_routing_context import NetworkObservation, RoutingContext  # noqa: E402


def build_showcase_context() -> RoutingContext:
    observation = NetworkObservation(
        time_index=10,
        node_ids=["N1", "N2", "N3"],
        link_ids=["L1", "L2", "L3"],
        degraded_links=["L2"],
        extra_delay_ms_by_link={},
        jammed_links=["L3"],
        malicious_drop_links=[],
        compromised_nodes=[],
        injected_delay_ms_by_link={},
    )

    return RoutingContext(
        scenario_name="showcase_demo",
        master_seed=42,
        time_index=10,
        source_node_id="N1",
        destination_node_id="N2",
        candidate_link_ids=["L2", "L3", "L1"],
        network_observation=observation,
        metadata={},
    )


def main() -> int:
    context = build_showcase_context()

    comparison_case = PolicyComparisonCase(
        case_id="mixed-risk-demo",
        context=context,
        candidate_link_ids=["L2", "L3", "L1"],
    )

    comparison_result = PolicyComparisonRunner().run_case(comparison_case)
    showcase_report = PolicyShowcaseBuilder().build(comparison_result)

    print(showcase_report.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())