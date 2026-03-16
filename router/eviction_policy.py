from typing import List, Protocol

from router.bundle import Bundle


class EvictionPolicy(Protocol):
    """
    Wave-45: Abstraction for storage pressure eviction strategies.
    Determines which bundles should be dropped when the node's store overflows.
    """
    def choose_victims(self, store: List[Bundle], bytes_to_free: int) -> List[Bundle]:
        ...


class DropLowestPriorityPolicy:
    """
    Wave-43 Default: Evicts bundles starting with the lowest priority.
    Tie-breakers: oldest created_at first, then lexical bundle.id.
    """
    def choose_victims(self, store: List[Bundle], bytes_to_free: int) -> List[Bundle]:
        candidates = sorted(
            store,
            key=lambda b: (b.priority, b.created_at, b.id)
        )
        
        victims = []
        freed = 0
        for victim in candidates:
            if freed >= bytes_to_free:
                break
            victims.append(victim)
            freed += victim.size_bytes
            
        return victims


class DropOldestPolicy:
    """
    Evicts the oldest bundles in the store regardless of their priority.
    Tie-breakers: lowest priority, then lexical bundle.id.
    """
    def choose_victims(self, store: List[Bundle], bytes_to_free: int) -> List[Bundle]:
        candidates = sorted(
            store,
            key=lambda b: (b.created_at, b.priority, b.id)
        )
        
        victims = []
        freed = 0
        for victim in candidates:
            if freed >= bytes_to_free:
                break
            victims.append(victim)
            freed += victim.size_bytes
            
        return victims