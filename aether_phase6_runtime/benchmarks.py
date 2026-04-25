from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import patch

from aether_routing_context import NetworkObservation, RoutingContext
from router.bundle import Bundle
from router.contact_manager import ContactManager
from router.route_scoring import RouteCandidate
from router.routing_policies import ScoredContactAwareRoutingPolicy

from .simulation_metrics import (
    SimulationRoutingMetric,
    SimulationRoutingMetricsCollector,
    SimulationRoutingMetricsSummary,
)


@dataclass(frozen=True)
class RuntimeBenchmarkScenario:
    """
    Deterministic input scenario for Phase-6/7 runtime benchmarking.
    """

    scenario_id: str
    candidate_link_ids: List[str]
    degraded_links: List[str]
    jammed_links: List[str]

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must be a non-empty string")

        object.__setattr__(self, "candidate_link_ids", list(self.candidate_link_ids))
        object.__setattr__(self, "degraded_links", list(self.degraded_links))
        object.__setattr__(self, "jammed_links", list(self.jammed_links))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "runtime_benchmark_scenario",
            "version": "1.0",
            "scenario_id": self.scenario_id,
            "candidate_link_ids": list(self.candidate_link_ids),
            "degraded_links": list(self.degraded_links),
            "jammed_links": list(self.jammed_links),
        }


@dataclass(frozen=True)
class RuntimeBenchmarkResult:
    """
    Stable outcome artifact representing one routing mode in one benchmark scenario.
    """

    scenario_id: str
    routing_mode: str
    selected_next_hop: Optional[str]
    decision_reason: str
    candidate_count_before: int
    candidate_count_after: int
    phase6_filtered_all: bool
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "runtime_benchmark_result",
            "version": "1.0",
            "scenario_id": self.scenario_id,
            "routing_mode": self.routing_mode,
            "selected_next_hop": self.selected_next_hop,
            "decision_reason": self.decision_reason,
            "candidate_count_before": self.candidate_count_before,
            "candidate_count_after": self.candidate_count_after,
            "phase6_filtered_all": self.phase6_filtered_all,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeBenchmarkSuiteResult:
    """
    Aggregated deterministic artifact for a complete runtime benchmark suite.
    """

    suite_id: str
    results: List[RuntimeBenchmarkResult]
    summary: SimulationRoutingMetricsSummary
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "results", list(self.results))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "runtime_benchmark_suite_result",
            "version": "1.0",
            "suite_id": self.suite_id,
            "results": [result.to_dict() for result in self.results],
            "summary": self.summary.to_dict(),
            "metadata": dict(self.metadata),
        }


def default_runtime_benchmark_scenarios() -> List[RuntimeBenchmarkScenario]:
    """
    Canonical deterministic runtime benchmark scenarios.
    """

    candidates = ["L1", "L2", "L3"]

    return [
        RuntimeBenchmarkScenario(
            scenario_id="clean",
            candidate_link_ids=candidates,
            degraded_links=[],
            jammed_links=[],
        ),
        RuntimeBenchmarkScenario(
            scenario_id="degraded",
            candidate_link_ids=candidates,
            degraded_links=["L2"],
            jammed_links=[],
        ),
        RuntimeBenchmarkScenario(
            scenario_id="jammed",
            candidate_link_ids=candidates,
            degraded_links=[],
            jammed_links=["L2"],
        ),
        RuntimeBenchmarkScenario(
            scenario_id="mixed_risk",
            candidate_link_ids=candidates,
            degraded_links=["L2"],
            jammed_links=["L3"],
        ),
    ]


class MockContactManager:
    """
    Minimal mock contact manager for benchmark use.

    Does NOT inherit from ContactManager to avoid constructor requirements.
    """

    def is_forwarding_allowed(
        self,
        source: str,
        destination: str,
        current_time: int,
    ) -> bool:
        return True


class RuntimeBenchmarkRunner:
    """
    Deterministic automation layer for comparing runtime routing modes
    across benchmark scenarios.
    """

    def __init__(self) -> None:
        self.modes = [
            ScoredContactAwareRoutingPolicy.ROUTING_MODE_LEGACY,
            ScoredContactAwareRoutingPolicy.ROUTING_MODE_PHASE6_BALANCED,
            ScoredContactAwareRoutingPolicy.ROUTING_MODE_PHASE6_ADAPTIVE,
        ]

    def _create_mock_candidate_routes(
        self,
        candidate_ids: List[str],
    ) -> Dict[str, Dict[str, List[RouteCandidate]]]:
        """
        Deterministic N1 -> N3 route candidates.

        Scores:
        - L2 = 90
        - L3 = 50
        - L1 = 10

        Legacy mode therefore prefers L2.
        """

        score_map = {
            "L1": 10.0,
            "L2": 90.0,
            "L3": 50.0,
        }

        candidates = [
            RouteCandidate(
                next_hop=link_id,
                score=score_map.get(link_id, 5.0),
            )
            for link_id in candidate_ids
        ]

        return {
            "N1": {
                "N3": candidates,
            }
        }

    def _create_minimal_bundle(self, destination: str) -> Bundle:
        """
        Create a benchmark bundle using the real project Bundle signature.
        """

        return Bundle(
            id="benchmark-b1",
            type="telemetry",
            source="N1",
            destination=destination,
            priority=1,
            created_at=0,
            ttl_sec=100,
            size_bytes=100,
            payload_ref="benchmark-payload",
            next_hop=None,
        )

    @staticmethod
    def _build_context_for_scenario(
        scenario: RuntimeBenchmarkScenario,
        current_node: str,
        destination: str,
        current_time: int,
        candidate_link_ids: List[str],
    ) -> RoutingContext:
        node_ids = sorted(set([current_node, destination] + candidate_link_ids))

        observation = NetworkObservation(
            time_index=current_time,
            node_ids=node_ids,
            link_ids=list(candidate_link_ids),
            degraded_links=list(scenario.degraded_links),
            extra_delay_ms_by_link={},
            jammed_links=list(scenario.jammed_links),
            malicious_drop_links=[],
            compromised_nodes=[],
            injected_delay_ms_by_link={},
        )

        return RoutingContext(
            scenario_name=f"benchmark_{scenario.scenario_id}",
            master_seed=42,
            time_index=current_time,
            source_node_id=current_node,
            destination_node_id=destination,
            candidate_link_ids=list(candidate_link_ids),
            network_observation=observation,
            metadata={
                "scenario_id": scenario.scenario_id,
                "benchmark": "runtime_benchmark_suite",
            },
        )

    def _estimate_candidate_count_after(
        self,
        policy: ScoredContactAwareRoutingPolicy,
        mode: str,
        scenario: RuntimeBenchmarkScenario,
    ) -> int:
        if mode == ScoredContactAwareRoutingPolicy.ROUTING_MODE_LEGACY:
            return len(scenario.candidate_link_ids)

        try:
            context = self._build_context_for_scenario(
                scenario=scenario,
                current_node="N1",
                destination="N3",
                current_time=0,
                candidate_link_ids=scenario.candidate_link_ids,
            )

            if mode == ScoredContactAwareRoutingPolicy.ROUTING_MODE_PHASE6_BALANCED:
                if policy._phase6_adapter is None:
                    return len(scenario.candidate_link_ids)
                return len(
                    policy._phase6_adapter.apply_decision(
                        context,
                        scenario.candidate_link_ids,
                    )
                )

            if mode == ScoredContactAwareRoutingPolicy.ROUTING_MODE_PHASE6_ADAPTIVE:
                if policy._adaptive_adapter is None:
                    return len(scenario.candidate_link_ids)
                return len(
                    policy._adaptive_adapter.apply_adaptive_decision(
                        context,
                        scenario.candidate_link_ids,
                        policy._neutral_adaptive_summary(),
                    )
                )

            return len(scenario.candidate_link_ids)

        except Exception:
            return len(scenario.candidate_link_ids)

    def run_suite(
        self,
        suite_id: str,
        scenarios: List[RuntimeBenchmarkScenario],
    ) -> RuntimeBenchmarkSuiteResult:
        results: List[RuntimeBenchmarkResult] = []
        collector = SimulationRoutingMetricsCollector()
        contact_manager = MockContactManager()
        bundle = self._create_minimal_bundle(destination="N3")

        for scenario in scenarios:
            candidate_routes = self._create_mock_candidate_routes(
                scenario.candidate_link_ids
            )

            for mode in self.modes:
                policy = ScoredContactAwareRoutingPolicy(
                    candidate_routes=candidate_routes,
                    contact_manager=contact_manager,
                    routing_mode=mode,
                )

                def mock_build_context(
                    current_node: str,
                    destination: str,
                    current_time: int,
                    candidate_link_ids: List[str],
                ) -> RoutingContext:
                    return self._build_context_for_scenario(
                        scenario=scenario,
                        current_node=current_node,
                        destination=destination,
                        current_time=current_time,
                        candidate_link_ids=candidate_link_ids,
                    )

                with patch.object(
                    policy,
                    "_build_minimal_context",
                    side_effect=mock_build_context,
                ):
                    decision = policy.evaluate_decision(
                        current_node="N1",
                        bundle=bundle,
                        current_time=0,
                    )

                count_before = len(scenario.candidate_link_ids)
                count_after = self._estimate_candidate_count_after(
                    policy=policy,
                    mode=mode,
                    scenario=scenario,
                )
                phase6_filtered_all = count_before > 0 and count_after == 0

                result = RuntimeBenchmarkResult(
                    scenario_id=scenario.scenario_id,
                    routing_mode=mode,
                    selected_next_hop=decision.next_hop,
                    decision_reason=decision.reason,
                    candidate_count_before=count_before,
                    candidate_count_after=count_after,
                    phase6_filtered_all=phase6_filtered_all,
                    metadata={
                        "runner_name": "RuntimeBenchmarkRunner",
                        "runner_version": "1.0",
                    },
                )

                results.append(result)

                collector.record(
                    SimulationRoutingMetric(
                        routing_mode=result.routing_mode,
                        selected_next_hop=result.selected_next_hop,
                        decision_reason=result.decision_reason,
                        candidate_count_before=result.candidate_count_before,
                        candidate_count_after=result.candidate_count_after,
                        phase6_filtered_all=result.phase6_filtered_all,
                    )
                )

        metadata = {
            "runner_name": "RuntimeBenchmarkRunner",
            "runner_version": "1.0",
            "scenario_count": len(scenarios),
            "mode_count": len(self.modes),
            "result_count": len(results),
        }

        return RuntimeBenchmarkSuiteResult(
            suite_id=suite_id,
            results=results,
            summary=collector.summary(),
            metadata=metadata,
        )