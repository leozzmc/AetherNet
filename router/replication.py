from dataclasses import dataclass
from typing import List, Optional

from router.routing_decision import RoutingDecision


@dataclass(frozen=True)
class ReplicationConfig:
    """
    Wave-49: Immutable configuration for replication control.
    Keeps default behavior strictly single-path (disabled).
    """
    enabled: bool = False
    mode: str = "bounded"
    max_replicas: int = 1


@dataclass(frozen=True)
class ReplicaTarget:
    """
    Describes a single intended hop for a bundle replica.
    """
    next_hop: str
    is_primary: bool
    rank: int


@dataclass(frozen=True)
class ReplicationPlan:
    """
    A deterministic execution plan for forwarding a bundle.
    Separates the INTENT to replicate from the actual RUNTIME copying.
    """
    enabled: bool
    primary_target: Optional[ReplicaTarget]
    replica_targets: List[ReplicaTarget]

    @property
    def total_copies(self) -> int:
        primary_count = 1 if self.primary_target else 0
        return primary_count + len(self.replica_targets)


class ReplicationPlanner:
    """
    Wave-49: Pure, deterministic helper to build replication plans.
    Does NOT mutate bundle state or execute forwarding.
    """

    @staticmethod
    def build_plan(
        decision: RoutingDecision,
        candidate_hops: List[str],
        config: ReplicationConfig
    ) -> ReplicationPlan:
        
        # Fallback 1: Replication is disabled or no primary route exists
        if not config.enabled or not decision.next_hop:
            primary = ReplicaTarget(decision.next_hop, True, 0) if decision.next_hop else None
            return ReplicationPlan(
                enabled=config.enabled,
                primary_target=primary,
                replica_targets=[]
            )

        # Fallback 2: Replication is enabled, but max_replicas restricts to 1
        if config.max_replicas <= 1:
            primary = ReplicaTarget(decision.next_hop, True, 0)
            return ReplicationPlan(
                enabled=True,
                primary_target=primary,
                replica_targets=[]
            )

        primary = ReplicaTarget(decision.next_hop, True, 0)
        replicas = []
        seen_hops = {decision.next_hop}
        rank = 1

        # We can only add (max_replicas - 1) additional targets
        max_additional = config.max_replicas - 1

        for hop in candidate_hops:
            if len(replicas) >= max_additional:
                break
            if hop not in seen_hops:
                replicas.append(ReplicaTarget(hop, False, rank))
                seen_hops.add(hop)
                rank += 1

        return ReplicationPlan(
            enabled=True,
            primary_target=primary,
            replica_targets=replicas
        )