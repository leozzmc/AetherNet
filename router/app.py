from __future__ import annotations

from typing import List, Optional

from metrics.congestion_metrics import CongestionMetrics
from router.bundle import Bundle
from router.contact_manager import ContactManager
from router.routing_policies import LegacyRoutingPolicy, StaticRoutingPolicy
from router.routing_policy import RoutingPolicy
from router.store_capacity import StoreCapacityController
from routing.routing_table import RoutingTable


class AetherRouter:
    """Minimal coordinator for routing-policy, contact-plan checks, and node storage."""

    def __init__(
        self,
        contact_manager: ContactManager,
        routing_table: Optional[RoutingTable] = None,
        routing_policy: Optional[RoutingPolicy] = None,
        store_capacity_bytes: Optional[int] = None,
    ):
        self.cm = contact_manager
        self.routing_table = routing_table
        self.routing_policy = routing_policy or self._default_policy(routing_table)
        
        # Wave-43: Congestion Control & Node Storage
        self.store: List[Bundle] = []
        self.capacity_controller = StoreCapacityController(store_capacity_bytes)
        self.congestion_metrics = CongestionMetrics(store_capacity_bytes)

    @staticmethod
    def _default_policy(routing_table: Optional[RoutingTable]) -> RoutingPolicy:
        """
        Preserve historical behavior:
        - explicit routing table takes precedence when provided
        - otherwise fall back to legacy static route policy
        """
        if routing_table is not None:
            return StaticRoutingPolicy(routing_table)
        return LegacyRoutingPolicy()

    def store_bundle(self, bundle: Bundle) -> List[Bundle]:
        """
        Wave-43: Safely enqueue a bundle into the node's store, enforcing finite 
        capacity and tracking congestion metrics. Returns any bundles dropped.
        """
        self.store.append(bundle)
        
        dropped = self.capacity_controller.enforce_capacity(self.store)
        
        self.congestion_metrics.record_drops(len(dropped))
        current_bytes = sum(b.size_bytes for b in self.store)
        self.congestion_metrics.update_store_bytes(current_bytes)
        
        return dropped

    def get_next_hop(
        self,
        current_node: str,
        destination: str,
        current_time: int = 0,
    ) -> str | None:
        """
        Preferred routing lookup entrypoint.
        """
        bundle = Bundle(
            id="__routing_lookup__",
            type="routing-lookup",
            source=current_node,
            destination=destination,
            priority=0,
            created_at=0,
            ttl_sec=1,
            size_bytes=0,
            payload_ref="routing-lookup",
        )
        # Assuming RoutingPolicy has select_next_hop (wrapper for evaluate_decision)
        return self.routing_policy.select_next_hop(
            current_node=current_node,
            bundle=bundle,
            current_time=current_time,
        )

    def next_hop(
        self,
        current_node: str,
        destination: str,
        current_time: int = 0,
    ) -> str | None:
        """Backward-compatible alias retained for older code/tests."""
        return self.get_next_hop(current_node, destination, current_time=current_time)

    def can_forward(self, current_node: str, bundle: Bundle, current_time: int) -> bool:
        next_node = self.routing_policy.select_next_hop(
            current_node=current_node,
            bundle=bundle,
            current_time=current_time,
        )
        if not next_node or next_node == current_node:
            return False
        return self.cm.is_forwarding_allowed(current_node, next_node, current_time)

    def can_forward_destination(self, current_node: str, destination: str, current_time: int) -> bool:
        next_node = self.get_next_hop(current_node, destination, current_time=current_time)
        if not next_node or next_node == current_node:
            return False
        return self.cm.is_forwarding_allowed(current_node, next_node, current_time)