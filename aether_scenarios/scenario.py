from typing import Any, Dict, List, Optional

from aether_adversarial import AdversarialTrace
from aether_reliability import LinkReliabilityTrace


class GeneratedScenario:
    """
    Replay-ready scenario artifact container.

    This object intentionally stores:
    - scenario identity
    - deterministic topology skeleton
    - optional reliability trace
    - optional adversarial trace
    - stable metadata

    It does NOT instantiate simulator runtime objects.
    """

    def __init__(
        self,
        scenario_name: str,
        master_seed: int,
        node_ids: List[str],
        link_ids: List[str],
        time_indices: List[int],
        metadata: Dict[str, Any],
        reliability_trace: Optional[LinkReliabilityTrace] = None,
        adversarial_trace: Optional[AdversarialTrace] = None,
    ) -> None:
        self.scenario_name = scenario_name
        self.master_seed = master_seed
        self.node_ids = list(node_ids)
        self.link_ids = list(link_ids)
        self.time_indices = list(time_indices)
        self.metadata = dict(metadata)
        self.reliability_trace = reliability_trace
        self.adversarial_trace = adversarial_trace

    def to_dict(self) -> Dict[str, Any]:
        """
        Export a stable, JSON-serializable representation of the scenario artifact.

        The returned structure must not expose internal mutable references.
        """
        return {
            "type": "scenario_artifact",
            "version": "1.0",
            "scenario_name": self.scenario_name,
            "master_seed": self.master_seed,
            "metadata": dict(self.metadata),
            "topology": {
                "node_count": len(self.node_ids),
                "link_count": len(self.link_ids),
                "time_horizon": len(self.time_indices),
                "node_ids": list(self.node_ids),
                "link_ids": list(self.link_ids),
                "time_indices": list(self.time_indices),
            },
            "reliability_trace": (
                self.reliability_trace.to_dict()
                if self.reliability_trace is not None
                else None
            ),
            "adversarial_trace": (
                self.adversarial_trace.to_dict()
                if self.adversarial_trace is not None
                else None
            ),
        }