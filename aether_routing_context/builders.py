from typing import Any, Dict, List, Optional

from aether_scenarios import GeneratedScenario

from .context import RoutingContext
from .observation import NetworkObservation


class ObservationBuilder:
    """
    Build a deterministic NetworkObservation from a GeneratedScenario at a
    specific time index.

    This builder treats the scenario and its traces as read-only inputs.
    """

    @staticmethod
    def _validate_time_index(scenario: GeneratedScenario, time_index: int) -> None:
        if time_index < 0:
            raise ValueError(f"time_index cannot be negative, got {time_index}")
        if time_index not in scenario.time_indices:
            raise ValueError(
                f"time_index {time_index} is not defined in scenario time indices"
            )

    def build(self, scenario: GeneratedScenario, time_index: int) -> NetworkObservation:
        self._validate_time_index(scenario, time_index)

        node_ids = sorted(scenario.node_ids)
        link_ids = sorted(scenario.link_ids)

        degraded_links: List[str] = []
        extra_delay_ms_by_link: Dict[str, int] = {}

        jammed_links: List[str] = []
        malicious_drop_links: List[str] = []
        compromised_nodes: List[str] = []
        injected_delay_ms_by_link: Dict[str, int] = {}

        if scenario.reliability_trace is not None:
            for link_id in link_ids:
                if scenario.reliability_trace.is_degraded(link_id, time_index):
                    degraded_links.append(link_id)

                extra_delay_ms = scenario.reliability_trace.get_extra_delay_ms(
                    link_id,
                    time_index,
                )
                if extra_delay_ms > 0:
                    extra_delay_ms_by_link[link_id] = extra_delay_ms

        if scenario.adversarial_trace is not None:
            for link_id in link_ids:
                if scenario.adversarial_trace.is_jammed(link_id, time_index):
                    jammed_links.append(link_id)

                if scenario.adversarial_trace.should_maliciously_drop(
                    link_id,
                    time_index,
                ):
                    malicious_drop_links.append(link_id)

                injected_delay_ms = scenario.adversarial_trace.get_injected_delay_ms(
                    link_id,
                    time_index,
                )
                if injected_delay_ms > 0:
                    injected_delay_ms_by_link[link_id] = injected_delay_ms

            for node_id in node_ids:
                if scenario.adversarial_trace.is_node_compromised(node_id, time_index):
                    compromised_nodes.append(node_id)

        return NetworkObservation(
            time_index=time_index,
            node_ids=node_ids,
            link_ids=link_ids,
            degraded_links=degraded_links,
            extra_delay_ms_by_link=extra_delay_ms_by_link,
            jammed_links=jammed_links,
            malicious_drop_links=malicious_drop_links,
            compromised_nodes=compromised_nodes,
            injected_delay_ms_by_link=injected_delay_ms_by_link,
        )


class RoutingContextBuilder:
    """
    Build a deterministic RoutingContext from a GeneratedScenario and routing task
    parameters.

    This builder validates:
    - source/destination node IDs
    - candidate link IDs
    - time index
    """

    def __init__(self) -> None:
        self._observation_builder = ObservationBuilder()

    @staticmethod
    def _validate_nodes(
        scenario: GeneratedScenario,
        source_node_id: str,
        destination_node_id: str,
    ) -> None:
        if source_node_id not in scenario.node_ids:
            raise ValueError(
                f"source_node_id {source_node_id} does not exist in scenario"
            )
        if destination_node_id not in scenario.node_ids:
            raise ValueError(
                f"destination_node_id {destination_node_id} does not exist in scenario"
            )

    @staticmethod
    def _validate_and_sort_candidate_links(
        scenario: GeneratedScenario,
        candidate_link_ids: List[str],
    ) -> List[str]:
        for link_id in candidate_link_ids:
            if link_id not in scenario.link_ids:
                raise ValueError(
                    f"candidate_link_id {link_id} does not exist in scenario"
                )
        return sorted(candidate_link_ids)

    def build(
        self,
        scenario: GeneratedScenario,
        time_index: int,
        source_node_id: str,
        destination_node_id: str,
        candidate_link_ids: Optional[List[str]] = None,
    ) -> RoutingContext:
        self._validate_nodes(scenario, source_node_id, destination_node_id)

        if candidate_link_ids is None:
            final_candidate_link_ids = sorted(scenario.link_ids)
        else:
            final_candidate_link_ids = self._validate_and_sort_candidate_links(
                scenario,
                candidate_link_ids,
            )

        network_observation = self._observation_builder.build(scenario, time_index)

        metadata: Dict[str, Any] = {
            "builder_name": "RoutingContextBuilder",
            "builder_version": "1.0",
            "has_reliability_trace": scenario.reliability_trace is not None,
            "has_adversarial_trace": scenario.adversarial_trace is not None,
            "candidate_link_count": len(final_candidate_link_ids),
        }

        return RoutingContext(
            scenario_name=scenario.scenario_name,
            master_seed=scenario.master_seed,
            time_index=time_index,
            source_node_id=source_node_id,
            destination_node_id=destination_node_id,
            candidate_link_ids=final_candidate_link_ids,
            network_observation=network_observation,
            metadata=metadata,
        )