from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class NetworkObservation:
    """
    Deterministic snapshot of network conditions at a single time index.

    This is an input abstraction for future adaptive routing logic.
    It intentionally summarizes scenario / trace state into a stable, exportable,
    read-only-style structure.
    """

    time_index: int
    node_ids: List[str]
    link_ids: List[str]

    degraded_links: List[str]
    extra_delay_ms_by_link: Dict[str, int]

    jammed_links: List[str]
    malicious_drop_links: List[str]
    compromised_nodes: List[str]
    injected_delay_ms_by_link: Dict[str, int]

    def __post_init__(self) -> None:
        object.__setattr__(self, "node_ids", list(self.node_ids))
        object.__setattr__(self, "link_ids", list(self.link_ids))
        object.__setattr__(self, "degraded_links", list(self.degraded_links))
        object.__setattr__(self, "jammed_links", list(self.jammed_links))
        object.__setattr__(self, "malicious_drop_links", list(self.malicious_drop_links))
        object.__setattr__(self, "compromised_nodes", list(self.compromised_nodes))
        object.__setattr__(
            self,
            "extra_delay_ms_by_link",
            dict(self.extra_delay_ms_by_link),
        )
        object.__setattr__(
            self,
            "injected_delay_ms_by_link",
            dict(self.injected_delay_ms_by_link),
        )

    @staticmethod
    def _sorted_dict(data: Dict[str, int]) -> Dict[str, int]:
        return {key: data[key] for key in sorted(data.keys())}

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a stable, JSON-serializable representation of the observation.

        Export order is stabilized even if a caller constructed this dataclass
        directly without using the builders.
        """
        return {
            "type": "network_observation",
            "version": "1.0",
            "time_index": self.time_index,
            "node_count": len(self.node_ids),
            "link_count": len(self.link_ids),
            "node_ids": sorted(self.node_ids),
            "link_ids": sorted(self.link_ids),
            "reliability_state": {
                "degraded_links": sorted(self.degraded_links),
                "extra_delay_ms_by_link": self._sorted_dict(self.extra_delay_ms_by_link),
            },
            "adversarial_state": {
                "jammed_links": sorted(self.jammed_links),
                "malicious_drop_links": sorted(self.malicious_drop_links),
                "compromised_nodes": sorted(self.compromised_nodes),
                "injected_delay_ms_by_link": self._sorted_dict(
                    self.injected_delay_ms_by_link
                ),
            },
        }