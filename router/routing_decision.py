from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RoutingDecision:
    """
    Wave-42: Represents a deterministic routing decision and its underlying reason.
    This provides observability into WHY a routing policy chose a specific next hop (or None).
    """
    next_hop: Optional[str]
    reason: str