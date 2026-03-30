from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class JammingEvent:
    link_id: str
    time_index: int
    jammed: bool


@dataclass(frozen=True)
class MaliciousDropEvent:
    link_id: str
    time_index: int
    drop: bool


@dataclass(frozen=True)
class DelayInjectionEvent:
    link_id: str
    time_index: int
    injected_delay_ms: int


@dataclass(frozen=True)
class NodeCompromiseEvent:
    node_id: str
    time_index: int
    compromised: bool


class AdversarialTrace:
    """
    Deterministic replay-ready adversarial trace.

    Scope:
    - link-level hostile conditions:
      - jamming
      - malicious drop
      - delay injection
    - node-level hostile conditions:
      - node compromise

    This structure is intentionally kept separate from Wave-74 reliability traces.
    Missing events fall back to safe defaults:
    - jammed => False
    - malicious drop => False
    - injected delay => 0
    - compromised => False
    """

    def __init__(self) -> None:
        self._jamming_events: Dict[Tuple[str, int], JammingEvent] = {}
        self._malicious_drop_events: Dict[Tuple[str, int], MaliciousDropEvent] = {}
        self._delay_injection_events: Dict[Tuple[str, int], DelayInjectionEvent] = {}
        self._node_compromise_events: Dict[Tuple[str, int], NodeCompromiseEvent] = {}

    @staticmethod
    def _link_key(link_id: str, time_index: int) -> Tuple[str, int]:
        return (link_id, time_index)

    @staticmethod
    def _node_key(node_id: str, time_index: int) -> Tuple[str, int]:
        return (node_id, time_index)

    @staticmethod
    def _sort_link_items(item: Tuple[Tuple[str, int], Any]) -> Tuple[str, int]:
        key, _ = item
        return (key[0], key[1])

    @staticmethod
    def _sort_node_items(item: Tuple[Tuple[str, int], Any]) -> Tuple[str, int]:
        key, _ = item
        return (key[0], key[1])

    def add_jamming_event(self, event: JammingEvent) -> None:
        self._jamming_events[self._link_key(event.link_id, event.time_index)] = event

    def add_malicious_drop_event(self, event: MaliciousDropEvent) -> None:
        self._malicious_drop_events[self._link_key(event.link_id, event.time_index)] = event

    def add_delay_injection_event(self, event: DelayInjectionEvent) -> None:
        self._delay_injection_events[self._link_key(event.link_id, event.time_index)] = event

    def add_node_compromise_event(self, event: NodeCompromiseEvent) -> None:
        self._node_compromise_events[self._node_key(event.node_id, event.time_index)] = event

    def is_jammed(self, link_id: str, time_index: int) -> bool:
        event = self._jamming_events.get(self._link_key(link_id, time_index))
        return event.jammed if event is not None else False

    def should_maliciously_drop(self, link_id: str, time_index: int) -> bool:
        event = self._malicious_drop_events.get(self._link_key(link_id, time_index))
        return event.drop if event is not None else False

    def get_injected_delay_ms(self, link_id: str, time_index: int) -> int:
        event = self._delay_injection_events.get(self._link_key(link_id, time_index))
        return event.injected_delay_ms if event is not None else 0

    def is_node_compromised(self, node_id: str, time_index: int) -> bool:
        event = self._node_compromise_events.get(self._node_key(node_id, time_index))
        return event.compromised if event is not None else False

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a stable JSON-serializable representation.

        Ordering contract:
        - link-level events sorted by (link_id, time_index)
        - node-level events sorted by (node_id, time_index)
        """
        jamming_events: List[Dict[str, Any]] = [
            asdict(event)
            for _, event in sorted(
                self._jamming_events.items(),
                key=self._sort_link_items,
            )
        ]
        malicious_drop_events: List[Dict[str, Any]] = [
            asdict(event)
            for _, event in sorted(
                self._malicious_drop_events.items(),
                key=self._sort_link_items,
            )
        ]
        delay_injection_events: List[Dict[str, Any]] = [
            asdict(event)
            for _, event in sorted(
                self._delay_injection_events.items(),
                key=self._sort_link_items,
            )
        ]
        node_compromise_events: List[Dict[str, Any]] = [
            asdict(event)
            for _, event in sorted(
                self._node_compromise_events.items(),
                key=self._sort_node_items,
            )
        ]

        return {
            "type": "adversarial_trace",
            "version": "1.0",
            "jamming_events": jamming_events,
            "malicious_drop_events": malicious_drop_events,
            "delay_injection_events": delay_injection_events,
            "node_compromise_events": node_compromise_events,
            "jamming_event_count": len(jamming_events),
            "malicious_drop_event_count": len(malicious_drop_events),
            "delay_injection_event_count": len(delay_injection_events),
            "node_compromise_event_count": len(node_compromise_events),
        }