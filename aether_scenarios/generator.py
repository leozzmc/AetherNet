from typing import Any, Dict, Optional

from aether_adversarial import AdversarialTrace, AdversarialTraceGenerator
from aether_random import RandomManager
from aether_reliability import LinkReliabilityTrace, ReliabilityTraceGenerator

from .scenario import GeneratedScenario
from .spec import ScenarioSpec


class ScenarioGenerator:
    """
    Deterministic scenario artifact generator.

    Wave-76 scope:
    - generate a topology skeleton (IDs + time indices)
    - optionally attach a reliability trace
    - optionally attach an adversarial trace
    - export stable scenario metadata

    This generator is a composition layer only.
    It does NOT instantiate simulator runtime objects.
    """

    @staticmethod
    def _build_node_ids(node_count: int) -> list[str]:
        return [f"N{i}" for i in range(1, node_count + 1)]

    @staticmethod
    def _build_link_ids(link_count: int) -> list[str]:
        return [f"L{i}" for i in range(1, link_count + 1)]

    @staticmethod
    def _build_time_indices(time_horizon: int) -> list[int]:
        return list(range(time_horizon))

    def generate(self, spec: ScenarioSpec) -> GeneratedScenario:
        random_manager = RandomManager(spec.master_seed)

        node_ids = self._build_node_ids(spec.node_count)
        link_ids = self._build_link_ids(spec.link_count)
        time_indices = self._build_time_indices(spec.time_horizon)

        reliability_trace: Optional[LinkReliabilityTrace] = None
        adversarial_trace: Optional[AdversarialTrace] = None

        reliability_stream_name: Optional[str] = None
        adversarial_stream_name: Optional[str] = None

        if spec.include_reliability_trace:
            reliability_stream_name = f"scenario::{spec.scenario_name}::reliability"
            reliability_generator = ReliabilityTraceGenerator(random_manager)
            reliability_trace = reliability_generator.generate_for_links(
                link_ids=link_ids,
                time_indices=time_indices,
                loss_probability=spec.loss_probability,
                max_extra_delay_ms=spec.max_extra_delay_ms,
                degradation_probability=spec.degradation_probability,
                stream_name=reliability_stream_name,
            )

        if spec.include_adversarial_trace:
            adversarial_stream_name = f"scenario::{spec.scenario_name}::adversarial"
            adversarial_generator = AdversarialTraceGenerator(random_manager)
            adversarial_trace = adversarial_generator.generate(
                link_ids=link_ids,
                node_ids=node_ids,
                time_indices=time_indices,
                jamming_probability=spec.jamming_probability,
                malicious_drop_probability=spec.malicious_drop_probability,
                max_injected_delay_ms=spec.max_injected_delay_ms,
                node_compromise_probability=spec.node_compromise_probability,
                stream_name=adversarial_stream_name,
            )

        metadata: Dict[str, Any] = {
            "generator_name": "ScenarioGenerator",
            "generator_version": "1.0",
            "has_reliability_trace": spec.include_reliability_trace,
            "has_adversarial_trace": spec.include_adversarial_trace,
            "node_count": spec.node_count,
            "link_count": spec.link_count,
            "time_horizon": spec.time_horizon,
            "stream_names": {
                "reliability": reliability_stream_name,
                "adversarial": adversarial_stream_name,
            },
        }

        return GeneratedScenario(
            scenario_name=spec.scenario_name,
            master_seed=spec.master_seed,
            node_ids=node_ids,
            link_ids=link_ids,
            time_indices=time_indices,
            metadata=metadata,
            reliability_trace=reliability_trace,
            adversarial_trace=adversarial_trace,
        )