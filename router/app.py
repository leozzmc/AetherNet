from __future__ import annotations

from typing import List, Optional

from metrics.congestion_metrics import CongestionMetrics
from router.bundle import Bundle
from router.contact_manager import ContactManager
from router.eviction_policy import DropLowestPriorityPolicy, EvictionPolicy
from router.failure_model import FailureModel
from router.routing_policies import LegacyRoutingPolicy, StaticRoutingPolicy
from router.routing_policy import RoutingPolicy
from router.store_capacity import StoreCapacityController
from routing.routing_table import RoutingTable
from router.replication import ReplicationConfig, ReplicationPlanner, ReplicationPlan


class AetherRouter:
    """
    Minimal coordinator for routing-policy, contact-plan checks, node storage, 
    hardware failure modeling, and replication planning.
    """

    def __init__(
        self,
        contact_manager: ContactManager,
        routing_table: Optional[RoutingTable] = None,
        routing_policy: Optional[RoutingPolicy] = None,
        store_capacity_bytes: Optional[int] = None,
        eviction_policy: Optional[EvictionPolicy] = None,
        failure_model: Optional[FailureModel] = None,
        replication_config: Optional[ReplicationConfig] = None,
    ):
        self.cm = contact_manager
        self.routing_table = routing_table
        self.routing_policy = routing_policy or self._default_policy(routing_table)
        
        # Wave-43/45: Congestion Control, Node Storage & Eviction Policy
        self.store: List[Bundle] = []
        actual_eviction_policy = eviction_policy or DropLowestPriorityPolicy()
        policy_name = actual_eviction_policy.__class__.__name__
        self.capacity_controller = StoreCapacityController(store_capacity_bytes, actual_eviction_policy)
        self.congestion_metrics = CongestionMetrics(store_capacity_bytes, policy_name)
        
        # Wave-47: Hardware Failure & Partition Modeling
        self.failure_model = failure_model
        
        # Wave-49: Replication Control Framework
        self.replication_config = replication_config or ReplicationConfig()

    @staticmethod
    def _default_policy(routing_table: Optional[RoutingTable]) -> RoutingPolicy:
        if routing_table is not None:
            return StaticRoutingPolicy(routing_table)
        return LegacyRoutingPolicy()

    def store_bundle(self, bundle: Bundle) -> List[Bundle]:
        self.store.append(bundle)
        dropped = self.capacity_controller.enforce_capacity(self.store)
        
        dropped_bytes = sum(b.size_bytes for b in dropped)
        self.congestion_metrics.record_drops(len(dropped), dropped_bytes)
        
        current_bytes = sum(b.size_bytes for b in self.store)
        self.congestion_metrics.update_store_bytes(current_bytes)
        
        return dropped

    def get_next_hop(self, current_node: str, destination: str, current_time: int = 0) -> str | None:
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
        return self.routing_policy.select_next_hop(current_node, bundle, current_time)

    def next_hop(self, current_node: str, destination: str, current_time: int = 0) -> str | None:
        return self.get_next_hop(current_node, destination, current_time=current_time)

    def can_forward(self, current_node: str, bundle: Bundle, current_time: int) -> bool:
        next_node = self.routing_policy.select_next_hop(current_node, bundle, current_time)
        if not next_node or next_node == current_node:
            return False
            
        if not self.cm.is_forwarding_allowed(current_node, next_node, current_time):
            return False
            
        if self.failure_model and not self.failure_model.is_forwarding_permitted(current_node, next_node, current_time):
            return False
            
        return True

    def can_forward_destination(self, current_node: str, destination: str, current_time: int) -> bool:
        next_node = self.get_next_hop(current_node, destination, current_time=current_time)
        if not next_node or next_node == current_node:
            return False
            
        if not self.cm.is_forwarding_allowed(current_node, next_node, current_time):
            return False
            
        if self.failure_model and not self.failure_model.is_forwarding_permitted(current_node, next_node, current_time):
            return False
            
        return True

    def get_replication_plan(self, current_node: str, bundle: Bundle, current_time: int) -> ReplicationPlan:
        """
        Wave-49: Generates a deterministic replication plan based on the routing policy
        and the node's replication configuration. 
        This separates the PLANNING of replication from the EXECUTION of transmission.
        """
        decision = self.routing_policy.evaluate_decision(current_node, bundle, current_time)
        
        candidate_hops = []
        if hasattr(self.routing_policy, "select_next_hops"):
            # If the policy supports multipath candidate generation, extract them
            candidate_hops = self.routing_policy.select_next_hops(current_node, bundle, current_time)
            
        return ReplicationPlanner.build_plan(
            decision=decision,
            candidate_hops=candidate_hops,
            config=self.replication_config
        )