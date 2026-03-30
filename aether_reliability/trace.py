from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class LossEvent:
    link_id: str
    time_index: int
    drop: bool


@dataclass(frozen=True)
class DelayEvent:
    link_id: str
    time_index: int
    extra_delay_ms: int


@dataclass(frozen=True)
class DegradationEvent:
    link_id: str
    time_index: int
    degraded: bool


class LinkReliabilityTrace:
    """
    Deterministic replay-ready reliability trace.

    This container keeps three event families separate:
    - loss
    - delay
    - degradation

    Missing events fall back to safe defaults:
    - drop => False
    - extra_delay_ms => 0
    - degraded => False
    """

    def __init__(self) -> None:
        self._loss_events: Dict[Tuple[str, int], LossEvent] = {}
        self._delay_events: Dict[Tuple[str, int], DelayEvent] = {}
        self._degradation_events: Dict[Tuple[str, int], DegradationEvent] = {}

    @staticmethod
    def _key(link_id: str, time_index: int) -> Tuple[str, int]:
        return (link_id, time_index)

    def add_loss_event(self, event: LossEvent) -> None:
        self._loss_events[self._key(event.link_id, event.time_index)] = event

    def add_delay_event(self, event: DelayEvent) -> None:
        self._delay_events[self._key(event.link_id, event.time_index)] = event

    def add_degradation_event(self, event: DegradationEvent) -> None:
        self._degradation_events[self._key(event.link_id, event.time_index)] = event

    def should_drop(self, link_id: str, time_index: int) -> bool:
        event = self._loss_events.get(self._key(link_id, time_index))
        return event.drop if event is not None else False

    def get_extra_delay_ms(self, link_id: str, time_index: int) -> int:
        event = self._delay_events.get(self._key(link_id, time_index))
        return event.extra_delay_ms if event is not None else 0

    def is_degraded(self, link_id: str, time_index: int) -> bool:
        event = self._degradation_events.get(self._key(link_id, time_index))
        return event.degraded if event is not None else False

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a stable JSON-serializable representation.

        Events are sorted deterministically by:
        - link_id
        - time_index
        """
        loss_events: List[Dict[str, Any]] = [
            asdict(event)
            for _, event in sorted(
                self._loss_events.items(),
                key=lambda item: (item[0][0], item[0][1]),
            )
        ]
        delay_events: List[Dict[str, Any]] = [
            asdict(event)
            for _, event in sorted(
                self._delay_events.items(),
                key=lambda item: (item[0][0], item[0][1]),
            )
        ]
        degradation_events: List[Dict[str, Any]] = [
            asdict(event)
            for _, event in sorted(
                self._degradation_events.items(),
                key=lambda item: (item[0][0], item[0][1]),
            )
        ]

        return {
            "type": "link_reliability_trace",
            "version": "1.0",
            "loss_events": loss_events,
            "delay_events": delay_events,
            "degradation_events": degradation_events,
            "loss_event_count": len(loss_events),
            "delay_event_count": len(delay_events),
            "degradation_event_count": len(degradation_events),
        }