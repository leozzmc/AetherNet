from typing import Optional
from bundle_queue.priority_queue import StrictPriorityQueue

class NodeRuntime:
    """
    Minimal structural abstraction representing a node in the AetherNet network.
    
    In Wave-22, this is strictly an in-process container. It binds a node's 
    identity to its primary outbound queue without implementing autonomous 
    routing or forwarding logic (which remains in the Simulator/Router).
    """
    def __init__(
        self, 
        node_id: str, 
        queue: StrictPriorityQueue, 
        role: Optional[str] = None
    ) -> None:
        self.node_id = node_id
        self.queue = queue
        self.role = role