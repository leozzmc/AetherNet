from typing import Dict, List, Tuple


class FailureModel:
    """
    Wave-47: Deterministic Failure & Partition Modeling Baseline.
    Acts as a runtime gate to suppress forwarding when a node is experiencing 
    an outage or a specific link has temporarily failed, despite the contact plan.
    """

    def __init__(
        self,
        node_outages: Dict[str, List[Tuple[int, int]]] = None,
        link_failures: List[Tuple[str, str, int, int]] = None,
    ):
        # Format: {"node_id": [(start_time, end_time), ...]}
        self.node_outages = node_outages or {}
        
        # Format: [("source", "target", start_time, end_time), ...]
        self.link_failures = link_failures or []

    def is_node_available(self, node_id: str, current_time: int) -> bool:
        """
        Check if a node is currently operational.
        An outage window is strictly [start_time, end_time).
        """
        outages = self.node_outages.get(node_id, [])
        for start, end in outages:
            if start <= current_time < end:
                return False
        return True

    def is_link_available(self, source: str, target: str, current_time: int) -> bool:
        """
        Check if a specific directional link is currently suffering a failure.
        A failure window is strictly [start_time, end_time).
        """
        for fail_src, fail_tgt, start, end in self.link_failures:
            if fail_src == source and fail_tgt == target:
                if start <= current_time < end:
                    return False
        return True

    def is_forwarding_permitted(self, source: str, target: str, current_time: int) -> bool:
        """
        Comprehensive check to determine if physical forwarding is possible at this exact tick.
        Forwarding is blocked if either the source or target node is down, 
        or if the specific link between them has failed.
        """
        if not self.is_node_available(source, current_time):
            return False
            
        if not self.is_node_available(target, current_time):
            return False
            
        if not self.is_link_available(source, target, current_time):
            return False
            
        return True