from dataclasses import dataclass
from typing import Any, Dict, List

from .link_signal import LinkSecuritySignal
from .node_signal import NodeSecuritySignal


@dataclass(frozen=True)
class SecuritySignalReport:
    """
    Aggregate deterministic security signal report for a routing context.
    """

    scenario_name: str
    time_index: int
    source_node_id: str
    destination_node_id: str
    link_signals: List[LinkSecuritySignal]
    node_signals: List[NodeSecuritySignal]
    summary: Dict[str, int]
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "link_signals", list(self.link_signals))
        object.__setattr__(self, "node_signals", list(self.node_signals))
        object.__setattr__(self, "summary", dict(self.summary))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @staticmethod
    def _sorted_dict(data: Dict[str, int]) -> Dict[str, int]:
        return {key: data[key] for key in sorted(data.keys())}

    def to_dict(self) -> Dict[str, Any]:
        sorted_link_signals = sorted(self.link_signals, key=lambda signal: signal.link_id)
        sorted_node_signals = sorted(self.node_signals, key=lambda signal: signal.node_id)

        exported_metadata = {
            "builder_name": self.metadata.get("builder_name"),
            "builder_version": self.metadata.get("builder_version"),
        }

        return {
            "type": "security_signal_report",
            "version": "1.0",
            "scenario_name": self.scenario_name,
            "time_index": self.time_index,
            "task": {
                "source_node_id": self.source_node_id,
                "destination_node_id": self.destination_node_id,
            },
            "summary": self._sorted_dict(self.summary),
            "metadata": exported_metadata,
            "link_signals": [signal.to_dict() for signal in sorted_link_signals],
            "node_signals": [signal.to_dict() for signal in sorted_node_signals],
        }