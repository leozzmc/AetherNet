from typing import List, Optional

from router.bundle import Bundle
from router.eviction_policy import DropLowestPriorityPolicy, EvictionPolicy


class StoreCapacityController:
    """
    Wave-43/45: Manages finite node storage capacity and delegates 
    overflow handling to an injected eviction policy.
    """

    def __init__(
        self, 
        capacity_bytes: Optional[int] = None,
        eviction_policy: Optional[EvictionPolicy] = None
    ):
        self.capacity_bytes = capacity_bytes
        self.eviction_policy = eviction_policy or DropLowestPriorityPolicy()

    def enforce_capacity(self, store: List[Bundle]) -> List[Bundle]:
        """
        Check current store usage. If it exceeds capacity, use the eviction 
        policy to deterministically select and drop bundles.
        """
        if self.capacity_bytes is None:
            return []

        total_bytes = sum(b.size_bytes for b in store)
        if total_bytes <= self.capacity_bytes:
            return []

        bytes_to_free = total_bytes - self.capacity_bytes
        victims = self.eviction_policy.choose_victims(store, bytes_to_free)
        
        for victim in victims:
            if victim in store:
                store.remove(victim)

        return victims