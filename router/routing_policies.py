from __future__ import annotations

from typing import Dict, List, Optional

from router.bundle import Bundle
from router.contact_manager import ContactManager
from router.policies import next_hop_for
from router.route_scoring import RouteCandidate, RouteScorer
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
        if current_node == bundle.destination:
            return None

        if bundle.next_hop:
            return bundle.next_hop

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
        if current_node == bundle.destination:
            return None

        if bundle.next_hop:
            if self.contact_manager.is_forwarding_allowed(current_node, bundle.next_hop, current_time):
                return bundle.next_hop
            return None

        candidate_hop = self.routing_table.get_next_hop(current_node, bundle.destination)
        if not candidate_hop:
            return None

        if self.contact_manager.is_forwarding_allowed(current_node, candidate_hop, current_time):
            return candidate_hop

        return None


class ScoredContactAwareRoutingPolicy:
    """
    Wave-40: Multi-candidate routing policy with deterministic scoring.
    Evaluates multiple potential next hops, filters out those without an active
    contact window, and selects the best remaining hop based on configured scores.
    """

    def __init__(
        self, 
        candidate_routes: Dict[str, Dict[str, List[RouteCandidate]]], 
        contact_manager: ContactManager
    ):
        # Format: source -> { destination -> [RouteCandidate(next_hop, score), ...] }
        self.candidate_routes = candidate_routes
        self.contact_manager = contact_manager

    def select_next_hop(
        self,
        current_node: str,
        bundle: Bundle,
        current_time: int,
    ) -> Optional[str]:
        # 1. Arrival semantics
        if current_node == bundle.destination:
            return None

        # 2. Explicit pinned next_hop takes precedence if contact is open
        if bundle.next_hop:
            if self.contact_manager.is_forwarding_allowed(current_node, bundle.next_hop, current_time):
                return bundle.next_hop
            return None

        # 3. Retrieve candidates for this specific (source, destination) pair
        dest_map = self.candidate_routes.get(current_node, {})
        candidates = dest_map.get(bundle.destination, [])
        
        if not candidates:
            return None

        # 4. Filter out candidates whose contact window is currently closed
        valid_candidates = []
        for candidate in candidates:
            if self.contact_manager.is_forwarding_allowed(current_node, candidate.next_hop, current_time):
                valid_candidates.append(candidate)

        # 5. Score and select the best candidate deterministically
        return RouteScorer.choose_best(valid_candidates)