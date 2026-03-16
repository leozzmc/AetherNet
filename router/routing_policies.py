from __future__ import annotations

from typing import Dict, List, Optional

from router.bundle import Bundle
from router.contact_graph import ContactForecast
from router.contact_manager import ContactManager
from router.policies import next_hop_for
from router.route_scoring import RouteCandidate, RouteScorer
from router.routing_policy import RoutingPolicy
from routing.routing_table import RoutingTable


class LegacyRoutingPolicy:
    """Preserve the original hardcoded route fallback behavior."""
    def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> Optional[str]:
        return next_hop_for(current_node, bundle.destination)


class StaticRoutingPolicy:
    """Wave-38: Baseline routing policy backed by the existing deterministic RoutingTable."""
    def __init__(self, routing_table: RoutingTable):
        self.routing_table = routing_table

    def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> Optional[str]:
        if current_node == bundle.destination:
            return None
        if bundle.next_hop:
            return bundle.next_hop
        return self.routing_table.get_next_hop(current_node, bundle.destination)


class ContactAwareRoutingPolicy:
    """Wave-39: Contact-aware routing policy. Requires the contact to be open NOW."""
    def __init__(self, routing_table: RoutingTable, contact_manager: ContactManager):
        self.routing_table = routing_table
        self.contact_manager = contact_manager

    def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> Optional[str]:
        if current_node == bundle.destination:
            return None
        if bundle.next_hop:
            if self.contact_manager.is_forwarding_allowed(current_node, bundle.next_hop, current_time):
                return bundle.next_hop
            return None
        candidate_hop = self.routing_table.get_next_hop(current_node, bundle.destination)
        if candidate_hop and self.contact_manager.is_forwarding_allowed(current_node, candidate_hop, current_time):
            return candidate_hop
        return None


class ScoredContactAwareRoutingPolicy:
    """Wave-40: Multi-candidate routing policy with deterministic scoring."""
    def __init__(self, candidate_routes: Dict[str, Dict[str, List[RouteCandidate]]], contact_manager: ContactManager):
        self.candidate_routes = candidate_routes
        self.contact_manager = contact_manager

    def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> Optional[str]:
        if current_node == bundle.destination:
            return None
        if bundle.next_hop:
            if self.contact_manager.is_forwarding_allowed(current_node, bundle.next_hop, current_time):
                return bundle.next_hop
            return None

        candidates = self.candidate_routes.get(current_node, {}).get(bundle.destination, [])
        valid_candidates = [
            c for c in candidates 
            if self.contact_manager.is_forwarding_allowed(current_node, c.next_hop, current_time)
        ]
        return RouteScorer.choose_best(valid_candidates)


class CGRLiteRoutingPolicy:
    """
    Wave-41: Bounded (2-hop) future-contact-aware routing policy.
    Evaluates candidate next hops based on when they can ultimately deliver the bundle,
    even if the first-hop contact is not currently open.
    """

    def __init__(self, candidate_routes: Dict[str, Dict[str, List[RouteCandidate]]], contact_manager: ContactManager):
        self.candidate_routes = candidate_routes
        self.forecast = ContactForecast(contact_manager)
        self.contact_manager = contact_manager

    def select_next_hop(
        self,
        current_node: str,
        bundle: Bundle,
        current_time: int,
    ) -> Optional[str]:
        
        if current_node == bundle.destination:
            return None

        # Explicit override semantics: keep it strictly backward-compatible.
        # Only allow the pinned route if it's currently open.
        if bundle.next_hop:
            if self.contact_manager.is_forwarding_allowed(current_node, bundle.next_hop, current_time):
                return bundle.next_hop
            return None

        candidates = self.candidate_routes.get(current_node, {}).get(bundle.destination, [])
        if not candidates:
            return None

        best_candidate = None
        best_arrival = float('inf')
        best_departure = float('inf')

        for candidate in candidates:
            next_hop = candidate.next_hop
            
            # Hop 1: Find the next available contact to the candidate
            first_hop = self.forecast.find_next_contact(current_node, next_hop, current_time)
            if not first_hop:
                continue
                
            arrival_time = None
            
            # Hop 2 (Bounded Lookahead): If candidate is the destination, we are done.
            if next_hop == bundle.destination:
                arrival_time = first_hop.estimated_arrival_time
            else:
                # Find the next contact from candidate to destination, strictly AFTER it arrives at the candidate
                second_hop = self.forecast.find_next_contact(next_hop, bundle.destination, first_hop.estimated_arrival_time)
                if not second_hop:
                    continue
                arrival_time = second_hop.estimated_arrival_time

            # Deterministic Tie-Breaker Evaluation
            if arrival_time < best_arrival:
                best_candidate = next_hop
                best_arrival = arrival_time
                best_departure = first_hop.start_time
            elif arrival_time == best_arrival:
                if first_hop.start_time < best_departure:
                    best_candidate = next_hop
                    best_departure = first_hop.start_time
                elif first_hop.start_time == best_departure:
                    # Lexical tie-break
                    if best_candidate is None or next_hop < best_candidate:
                        best_candidate = next_hop

        return best_candidate