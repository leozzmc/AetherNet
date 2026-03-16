from __future__ import annotations

from typing import Dict, List, Optional

from router.bundle import Bundle
from router.contact_graph import ContactForecast
from router.contact_manager import ContactManager
from router.policies import next_hop_for
from router.route_scoring import RouteCandidate, RouteScorer
from router.routing_decision import RoutingDecision
from router.routing_policy import RoutingPolicy
from routing.routing_table import RoutingTable


class LegacyRoutingPolicy:
    """Preserve the original hardcoded route fallback behavior."""

    def evaluate_decision(self, current_node: str, bundle: Bundle, current_time: int) -> RoutingDecision:
        hop = next_hop_for(current_node, bundle.destination)
        if hop:
            return RoutingDecision(next_hop=hop, reason="selected_legacy_route")
        return RoutingDecision(next_hop=None, reason="no_route")

    def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> Optional[str]:
        return self.evaluate_decision(current_node, bundle, current_time).next_hop


class StaticRoutingPolicy:
    """Wave-38: Baseline routing policy backed by the existing deterministic RoutingTable."""

    def __init__(self, routing_table: RoutingTable):
        self.routing_table = routing_table

    def evaluate_decision(self, current_node: str, bundle: Bundle, current_time: int) -> RoutingDecision:
        if current_node == bundle.destination:
            return RoutingDecision(next_hop=None, reason="at_destination")

        if bundle.next_hop:
            return RoutingDecision(next_hop=bundle.next_hop, reason="explicit_override_open")

        candidate_hop = self.routing_table.get_next_hop(current_node, bundle.destination)
        if candidate_hop:
            return RoutingDecision(next_hop=candidate_hop, reason="selected_static_route")
            
        return RoutingDecision(next_hop=None, reason="no_route")

    def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> Optional[str]:
        return self.evaluate_decision(current_node, bundle, current_time).next_hop


class ContactAwareRoutingPolicy:
    """Wave-39: Contact-aware routing policy. Requires the contact to be open NOW."""

    def __init__(self, routing_table: RoutingTable, contact_manager: ContactManager):
        self.routing_table = routing_table
        self.contact_manager = contact_manager

    def evaluate_decision(self, current_node: str, bundle: Bundle, current_time: int) -> RoutingDecision:
        if current_node == bundle.destination:
            return RoutingDecision(next_hop=None, reason="at_destination")

        if bundle.next_hop:
            if self.contact_manager.is_forwarding_allowed(current_node, bundle.next_hop, current_time):
                return RoutingDecision(next_hop=bundle.next_hop, reason="explicit_override_open")
            return RoutingDecision(next_hop=None, reason="explicit_override_blocked")

        candidate_hop = self.routing_table.get_next_hop(current_node, bundle.destination)
        if not candidate_hop:
            return RoutingDecision(next_hop=None, reason="no_route")

        if self.contact_manager.is_forwarding_allowed(current_node, candidate_hop, current_time):
            return RoutingDecision(next_hop=candidate_hop, reason="selected_static_route")

        return RoutingDecision(next_hop=None, reason="contact_blocked")

    def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> Optional[str]:
        return self.evaluate_decision(current_node, bundle, current_time).next_hop


class ScoredContactAwareRoutingPolicy:
    """Wave-40: Multi-candidate routing policy with deterministic scoring."""

    def __init__(self, candidate_routes: Dict[str, Dict[str, List[RouteCandidate]]], contact_manager: ContactManager):
        self.candidate_routes = candidate_routes
        self.contact_manager = contact_manager

    def evaluate_decision(self, current_node: str, bundle: Bundle, current_time: int) -> RoutingDecision:
        if current_node == bundle.destination:
            return RoutingDecision(next_hop=None, reason="at_destination")

        if bundle.next_hop:
            if self.contact_manager.is_forwarding_allowed(current_node, bundle.next_hop, current_time):
                return RoutingDecision(next_hop=bundle.next_hop, reason="explicit_override_open")
            return RoutingDecision(next_hop=None, reason="explicit_override_blocked")

        candidates = self.candidate_routes.get(current_node, {}).get(bundle.destination, [])
        if not candidates:
            return RoutingDecision(next_hop=None, reason="no_route")

        valid_candidates = [
            c for c in candidates
            if self.contact_manager.is_forwarding_allowed(current_node, c.next_hop, current_time)
        ]

        if not valid_candidates:
            return RoutingDecision(next_hop=None, reason="contact_blocked")

        best_hop = RouteScorer.choose_best(valid_candidates)
        return RoutingDecision(next_hop=best_hop, reason="selected_scored_candidate")

    def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> Optional[str]:
        return self.evaluate_decision(current_node, bundle, current_time).next_hop


class CGRLiteRoutingPolicy:
    """Wave-41: Bounded 2-hop future-contact-aware routing policy."""

    def __init__(self, candidate_routes: Dict[str, Dict[str, List[RouteCandidate]]], contact_manager: ContactManager):
        self.candidate_routes = candidate_routes
        self.contact_manager = contact_manager
        self.forecast = ContactForecast(contact_manager)

    def evaluate_decision(self, current_node: str, bundle: Bundle, current_time: int) -> RoutingDecision:
        if current_node == bundle.destination:
            return RoutingDecision(next_hop=None, reason="at_destination")

        if bundle.next_hop:
            if self.contact_manager.is_forwarding_allowed(current_node, bundle.next_hop, current_time):
                return RoutingDecision(next_hop=bundle.next_hop, reason="explicit_override_open")
            return RoutingDecision(next_hop=None, reason="explicit_override_blocked")

        candidates = self.candidate_routes.get(current_node, {}).get(bundle.destination, [])
        if not candidates:
            return RoutingDecision(next_hop=None, reason="no_route")

        best_candidate: Optional[str] = None
        best_arrival: Optional[int] = None
        best_departure: Optional[int] = None

        for candidate in candidates:
            next_hop = candidate.next_hop

            first_hop = self.forecast.find_next_contact(current_node, next_hop, current_time)
            if first_hop is None:
                continue

            if next_hop == bundle.destination:
                estimated_arrival = first_hop.estimated_arrival_time
            else:
                second_hop = self.forecast.find_next_contact(
                    next_hop,
                    bundle.destination,
                    first_hop.estimated_arrival_time,
                )
                if second_hop is None:
                    continue
                estimated_arrival = second_hop.estimated_arrival_time

            departure_time = first_hop.start_time

            if best_candidate is None:
                best_candidate = next_hop
                best_arrival = estimated_arrival
                best_departure = departure_time
                continue

            assert best_arrival is not None
            assert best_departure is not None

            if estimated_arrival < best_arrival:
                best_candidate = next_hop
                best_arrival = estimated_arrival
                best_departure = departure_time
            elif estimated_arrival == best_arrival:
                if departure_time < best_departure:
                    best_candidate = next_hop
                    best_departure = departure_time
                elif departure_time == best_departure and next_hop < best_candidate:
                    best_candidate = next_hop

        if best_candidate is None:
            return RoutingDecision(next_hop=None, reason="no_future_route")

        return RoutingDecision(next_hop=best_candidate, reason="selected_future_route")

    def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> Optional[str]:
        return self.evaluate_decision(current_node, bundle, current_time).next_hop


class OpportunisticRoutingPolicy:
    """Wave-46: Bounded Opportunistic Hold-vs-Forward Baseline."""

    def __init__(
        self, 
        candidate_routes: Dict[str, Dict[str, List[RouteCandidate]]], 
        contact_manager: ContactManager,
        hold_window: int = 20
    ):
        self.candidate_routes = candidate_routes
        self.contact_manager = contact_manager
        self.hold_window = hold_window

    def _get_candidate_by_name(self, candidates: List[RouteCandidate], name: str) -> Optional[RouteCandidate]:
        for c in candidates:
            if c.next_hop == name:
                return c
        return None

    def evaluate_decision(self, current_node: str, bundle: Bundle, current_time: int) -> RoutingDecision:
        if current_node == bundle.destination:
            return RoutingDecision(next_hop=None, reason="at_destination")

        if bundle.next_hop:
            if self.contact_manager.is_forwarding_allowed(current_node, bundle.next_hop, current_time):
                return RoutingDecision(next_hop=bundle.next_hop, reason="explicit_override_open")
            return RoutingDecision(next_hop=None, reason="explicit_override_blocked")

        candidates = self.candidate_routes.get(current_node, {}).get(bundle.destination, [])
        if not candidates:
            return RoutingDecision(next_hop=None, reason="no_route")

        open_candidates = []
        future_candidates = []
        window_end = current_time + self.hold_window

        for c in candidates:
            if self.contact_manager.is_forwarding_allowed(current_node, c.next_hop, current_time):
                open_candidates.append(c)
            else:
                opens_soon = False
                for contact in self.contact_manager.contacts:
                    if contact.allows(current_node, c.next_hop):
                        if current_time < contact.start_time <= window_end:
                            opens_soon = True
                            break
                if opens_soon:
                    future_candidates.append(c)

        best_open_name = RouteScorer.choose_best(open_candidates)
        best_future_name = RouteScorer.choose_best(future_candidates)

        if not best_open_name and not best_future_name:
            return RoutingDecision(next_hop=None, reason="no_opportunity")

        if not best_open_name and best_future_name:
            return RoutingDecision(next_hop=None, reason="hold_for_better_contact")

        if best_open_name and best_future_name:
            best_open_obj = self._get_candidate_by_name(candidates, best_open_name)
            best_future_obj = self._get_candidate_by_name(candidates, best_future_name)
            
            assert best_open_obj is not None
            assert best_future_obj is not None

            if best_future_obj.score > best_open_obj.score:
                return RoutingDecision(next_hop=None, reason="hold_for_better_contact")

        return RoutingDecision(next_hop=best_open_name, reason="selected_opportunistic_now")

    def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> Optional[str]:
        return self.evaluate_decision(current_node, bundle, current_time).next_hop


class MultiPathRoutingPolicy:
    """
    Wave-48: Bounded Multi-Path Candidate Selection Baseline.
    Evaluates multiple open contacts and selects the top-K candidates deterministically 
    based on score and lexical order, without engaging in uncontrolled replication.
    Maintains backward compatibility by falling back to the top-1 choice for existing APIs.
    """

    def __init__(
        self,
        candidate_routes: Dict[str, Dict[str, List[RouteCandidate]]],
        contact_manager: ContactManager,
        max_paths: int = 2
    ):
        self.candidate_routes = candidate_routes
        self.contact_manager = contact_manager
        self.max_paths = max_paths

    def select_next_hops(self, current_node: str, bundle: Bundle, current_time: int) -> List[str]:
        """
        Wave-48 primary API: Selects up to `max_paths` valid and open next hops deterministically.
        """
        if current_node == bundle.destination:
            return []

        # Explicit override takes absolute precedence if open
        if bundle.next_hop:
            if self.contact_manager.is_forwarding_allowed(current_node, bundle.next_hop, current_time):
                return [bundle.next_hop]
            return []

        candidates = self.candidate_routes.get(current_node, {}).get(bundle.destination, [])
        
        # Filter strictly for currently open contacts
        valid_candidates = [
            c for c in candidates
            if self.contact_manager.is_forwarding_allowed(current_node, c.next_hop, current_time)
        ]

        if not valid_candidates:
            return []

        # Sort deterministically: highest score first, lexical order tie-break
        sorted_candidates = sorted(
            valid_candidates,
            key=lambda c: (-c.score, c.next_hop)
        )

        return [c.next_hop for c in sorted_candidates[:self.max_paths]]

    def evaluate_decision(self, current_node: str, bundle: Bundle, current_time: int) -> RoutingDecision:
        """
        Maintains Wave-42 metrics compatibility by reporting the primary (first) decision.
        """
        if current_node == bundle.destination:
            return RoutingDecision(next_hop=None, reason="at_destination")

        if bundle.next_hop:
            if self.contact_manager.is_forwarding_allowed(current_node, bundle.next_hop, current_time):
                return RoutingDecision(next_hop=bundle.next_hop, reason="explicit_override_open")
            return RoutingDecision(next_hop=None, reason="explicit_override_blocked")

        candidates = self.candidate_routes.get(current_node, {}).get(bundle.destination, [])
        if not candidates:
            return RoutingDecision(next_hop=None, reason="no_route")

        hops = self.select_next_hops(current_node, bundle, current_time)
        if not hops:
            return RoutingDecision(next_hop=None, reason="contact_blocked")

        return RoutingDecision(next_hop=hops[0], reason="selected_multipath_candidate")

    def select_next_hop(self, current_node: str, bundle: Bundle, current_time: int) -> Optional[str]:
        """
        Maintains Phase-3 API compatibility by degrading cleanly to the top-1 choice.
        """
        return self.evaluate_decision(current_node, bundle, current_time).next_hop