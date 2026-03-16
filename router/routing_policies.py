from __future__ import annotations

from typing import Optional

from router.bundle import Bundle
from router.contact_manager import ContactManager
from router.policies import next_hop_for
from router.routing_policy import RoutingPolicy
from routing.routing_table import RoutingTable


class LegacyRoutingPolicy:
    """Preserve the original hardcoded route fallback behavior."""

    def select_next_hop(
        self,
        current_node: str,
        bundle: Bundle,
        current_time: int,
    ) -> Optional[str]:
        return next_hop_for(current_node, bundle.destination)


class StaticRoutingPolicy:
    """
    Wave-38: Baseline routing policy backed by the existing deterministic RoutingTable.
    Explicitly defines destination arrival and no-route semantics.
    """

    def __init__(self, routing_table: RoutingTable):
        self.routing_table = routing_table

    def select_next_hop(
        self,
        current_node: str,
        bundle: Bundle,
        current_time: int,
    ) -> Optional[str]:
        # 1. Arrival semantics: Do not forward if we are already at the destination
        if current_node == bundle.destination:
            return None

        # 2. Override semantics: Explicit pinned next_hop takes absolute precedence
        if bundle.next_hop:
            return bundle.next_hop

        # 3. Table lookup semantics: Returns None implicitly if route/source is unknown
        return self.routing_table.get_next_hop(current_node, bundle.destination)


class ContactAwareRoutingPolicy:
    """
    Wave-39: Contact-aware routing policy.
    Determines the next hop by checking both a static routing table (for the path)
    and the contact manager (for current link availability).
    Returns a next hop ONLY if the route exists AND the contact is open at current_time.
    """

    def __init__(self, routing_table: RoutingTable, contact_manager: ContactManager):
        self.routing_table = routing_table
        self.contact_manager = contact_manager

    def select_next_hop(
        self,
        current_node: str,
        bundle: Bundle,
        current_time: int,
    ) -> Optional[str]:
        # 1. Arrival semantics: Do not forward if we are already at the destination
        if current_node == bundle.destination:
            return None

        # 2. Explicit pinned next_hop takes precedence, BUT must be contact-aware
        if bundle.next_hop:
            if self.contact_manager.is_forwarding_allowed(current_node, bundle.next_hop, current_time):
                return bundle.next_hop
            return None

        # 3. Resolve the theoretical next hop from the static routing table
        candidate_hop = self.routing_table.get_next_hop(current_node, bundle.destination)
        if not candidate_hop:
            return None  # No route exists

        # 4. Gating: Only return the candidate if the contact is open right now
        if self.contact_manager.is_forwarding_allowed(current_node, candidate_hop, current_time):
            return candidate_hop

        # 5. Route exists, but contact is currently closed
        return None