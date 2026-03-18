from dataclasses import dataclass
from typing import List, Optional

from router.routing_decision import RoutingDecision


@dataclass(frozen=True)
class ReplicationConfig:
    """
    Wave-49: Immutable configuration for replication control.
    Defaults preserve existing single-path behavior.
    """
    enabled: bool = False
    mode: str = "bounded"
    max_replicas: int = 1


@dataclass(frozen=True)
class ReplicaTarget:
    """
    Describes one intended forwarding target in a replication plan.
    """
    next_hop: str
    is_primary: bool
    rank: int


@dataclass(frozen=True)
class ReplicationPlan:
    """
    Deterministic replication plan.

    This is a planning abstraction only. It does not execute replication.
    """
    enabled: bool
    primary_target: Optional[ReplicaTarget]
    replica_targets: List[ReplicaTarget]

    @property
    def total_copies(self) -> int:
        primary_count = 1 if self.primary_target is not None else 0
        return primary_count + len(self.replica_targets)


class ReplicationPlanner:
    """
    Wave-49: Pure deterministic helper for constructing replication plans.
    """

    @staticmethod
    def build_plan(
        decision: RoutingDecision,
        candidate_hops: List[str],
        config: ReplicationConfig,
    ) -> ReplicationPlan:
        # No selected route -> no copies
        if decision.next_hop is None:
            return ReplicationPlan(
                enabled=config.enabled,
                primary_target=None,
                replica_targets=[],
            )

        primary = ReplicaTarget(
            next_hop=decision.next_hop,
            is_primary=True,
            rank=0,
        )

        # Backward-compatible default: no extra replicas
        if not config.enabled or config.max_replicas <= 1:
            return ReplicationPlan(
                enabled=config.enabled,
                primary_target=primary,
                replica_targets=[],
            )

        max_additional = config.max_replicas - 1
        replicas: List[ReplicaTarget] = []
        seen = {decision.next_hop}
        next_rank = 1

        for hop in candidate_hops:
            if len(replicas) >= max_additional:
                break
            if hop in seen:
                continue

            replicas.append(
                ReplicaTarget(
                    next_hop=hop,
                    is_primary=False,
                    rank=next_rank,
                )
            )
            seen.add(hop)
            next_rank += 1

        return ReplicationPlan(
            enabled=True,
            primary_target=primary,
            replica_targets=replicas,
        )