from typing import List

from aether_random import RandomManager
from aether_adversarial.trace import (
    AdversarialTrace,
    DelayInjectionEvent,
    JammingEvent,
    MaliciousDropEvent,
    NodeCompromiseEvent,
)


class AdversarialTraceGenerator:
    """
    Deterministic adversarial trace generator.

    Generation contract for deterministic replay:
    1. link_ids are processed in sorted ascending order
    2. node_ids are processed in sorted ascending order
    3. time_indices are processed in sorted ascending order
    4. all link-level draws occur before node-level draws
    5. for each (link_id, time_index), draw order is:
       - jamming
       - malicious drop
       - delay injection

    This explicit ordering is part of the trace reproducibility contract and
    should not be changed casually in later waves.
    """

    def __init__(self, random_manager: RandomManager) -> None:
        self._rm = random_manager

    @staticmethod
    def _validate_probability(name: str, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be between 0.0 and 1.0, got {value}")

    @staticmethod
    def _validate_max_injected_delay_ms(value: int) -> None:
        if value < 0:
            raise ValueError(f"max_injected_delay_ms must be >= 0, got {value}")

    def generate(
        self,
        link_ids: List[str],
        node_ids: List[str],
        time_indices: List[int],
        jamming_probability: float = 0.0,
        malicious_drop_probability: float = 0.0,
        max_injected_delay_ms: int = 0,
        node_compromise_probability: float = 0.0,
        stream_name: str = "adversarial_trace",
    ) -> AdversarialTrace:
        self._validate_probability("jamming_probability", jamming_probability)
        self._validate_probability(
            "malicious_drop_probability",
            malicious_drop_probability,
        )
        self._validate_probability(
            "node_compromise_probability",
            node_compromise_probability,
        )
        self._validate_max_injected_delay_ms(max_injected_delay_ms)

        trace = AdversarialTrace()

        sorted_links = sorted(link_ids)
        sorted_nodes = sorted(node_ids)
        sorted_times = sorted(time_indices)

        full_stream_name = f"adversarial_trace::{stream_name}"
        stream = self._rm.create_stream(full_stream_name)

        for link_id in sorted_links:
            for time_index in sorted_times:
                jammed = stream.random() < jamming_probability
                malicious_drop = stream.random() < malicious_drop_probability
                injected_delay_ms = (
                    stream.randint(0, max_injected_delay_ms)
                    if max_injected_delay_ms > 0
                    else 0
                )

                if jammed:
                    trace.add_jamming_event(
                        JammingEvent(
                            link_id=link_id,
                            time_index=time_index,
                            jammed=True,
                        )
                    )

                if malicious_drop:
                    trace.add_malicious_drop_event(
                        MaliciousDropEvent(
                            link_id=link_id,
                            time_index=time_index,
                            drop=True,
                        )
                    )

                if injected_delay_ms > 0:
                    trace.add_delay_injection_event(
                        DelayInjectionEvent(
                            link_id=link_id,
                            time_index=time_index,
                            injected_delay_ms=injected_delay_ms,
                        )
                    )

        for node_id in sorted_nodes:
            for time_index in sorted_times:
                compromised = stream.random() < node_compromise_probability

                if compromised:
                    trace.add_node_compromise_event(
                        NodeCompromiseEvent(
                            node_id=node_id,
                            time_index=time_index,
                            compromised=True,
                        )
                    )

        return trace