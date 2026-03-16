from typing import List, Optional

from router.bundle import Bundle


class StoreCapacityController:
    """
    Wave-43: Manages finite node storage capacity and enforces deterministic
    overflow drop policies.
    """

    def __init__(self, capacity_bytes: Optional[int] = None):
        # None implies infinite capacity (backward compatibility)
        self.capacity_bytes = capacity_bytes

    def enforce_capacity(self, store: List[Bundle]) -> List[Bundle]:
        """
        Check current store usage. If it exceeds capacity, deterministically 
        drop bundles until it fits.
        
        Drop Policy: drop_lowest_priority
        Tie-breakers: oldest created_at first, then lexical bundle.id
        """
        if self.capacity_bytes is None:
            return []

        total_bytes = sum(b.size_bytes for b in store)
        if total_bytes <= self.capacity_bytes:
            return []

        # Deterministic sorting for drop candidates:
        # 1. Lowest priority first (smaller number = lower priority to drop first)
        # 2. Oldest created_at first
        # 3. Lexical bundle id tie-breaker
        drop_candidates = sorted(
            store,
            key=lambda b: (b.priority, b.created_at, b.id)
        )

        dropped_bundles = []
        
        while total_bytes > self.capacity_bytes and drop_candidates:
            victim = drop_candidates.pop(0)
            store.remove(victim)
            dropped_bundles.append(victim)
            total_bytes -= victim.size_bytes

        return dropped_bundles