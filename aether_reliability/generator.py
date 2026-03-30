from typing import List

from aether_random import RandomManager
from aether_reliability.trace import (
    DelayEvent,
    DegradationEvent,
    LinkReliabilityTrace,
    LossEvent,
)


class ReliabilityTraceGenerator:
    """
    Deterministic reliability trace generator.

    Wave-74 scope:
    - generate replay-ready loss / delay / degradation traces
    - do not modify simulator runtime behavior
    """

    def __init__(self, random_manager: RandomManager) -> None:
        self._random_manager = random_manager

    @staticmethod
    def _validate_probability(name: str, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be between 0.0 and 1.0, got {value}")

    @staticmethod
    def _validate_max_extra_delay_ms(value: int) -> None:
        if value < 0:
            raise ValueError(f"max_extra_delay_ms must be >= 0, got {value}")

    def generate_for_links(
        self,
        link_ids: List[str],
        time_indices: List[int],
        loss_probability: float = 0.0,
        max_extra_delay_ms: int = 0,
        degradation_probability: float = 0.0,
        stream_name: str = "reliability_trace",
    ) -> LinkReliabilityTrace:
        self._validate_probability("loss_probability", loss_probability)
        self._validate_probability("degradation_probability", degradation_probability)
        self._validate_max_extra_delay_ms(max_extra_delay_ms)

        trace = LinkReliabilityTrace()

        sorted_links = sorted(link_ids)
        sorted_time_indices = sorted(time_indices)

        full_stream_name = f"reliability_trace::{stream_name}"
        stream = self._random_manager.create_stream(full_stream_name)

        for link_id in sorted_links:
            for time_index in sorted_time_indices:
                drop = stream.random() < loss_probability
                degraded = stream.random() < degradation_probability
                extra_delay_ms = (
                    stream.randint(0, max_extra_delay_ms)
                    if max_extra_delay_ms > 0
                    else 0
                )

                if drop:
                    trace.add_loss_event(
                        LossEvent(
                            link_id=link_id,
                            time_index=time_index,
                            drop=True,
                        )
                    )

                if extra_delay_ms > 0:
                    trace.add_delay_event(
                        DelayEvent(
                            link_id=link_id,
                            time_index=time_index,
                            extra_delay_ms=extra_delay_ms,
                        )
                    )

                if degraded:
                    trace.add_degradation_event(
                        DegradationEvent(
                            link_id=link_id,
                            time_index=time_index,
                            degraded=True,
                        )
                    )

        return trace