from collections import deque
from typing import Dict, Optional

from router.bundle import Bundle


class DropDecision:
    """
    Result of evaluating whether an incoming bundle should be admitted
    into a full queue.
    """

    def __init__(self, admit_incoming: bool, evicted_bundle: Optional[Bundle] = None) -> None:
        self.admit_incoming = admit_incoming
        self.evicted_bundle = evicted_bundle


class DropLowestPriorityPolicy:
    """
    Deterministic queue congestion policy.

    Rules:
    - If incoming bundle has strictly higher priority than the lowest-priority
      existing bundle, evict the oldest bundle from that lowest-priority class
      and admit the incoming bundle.
    - Otherwise reject the incoming bundle.
    - Equal priority is treated conservatively: reject incoming.
    """

    def evaluate(
        self,
        incoming_bundle: Bundle,
        current_queues: Dict[int, deque[Bundle]],
        current_size: int,
        max_size: int,
    ) -> DropDecision:
        if current_size < max_size:
            return DropDecision(admit_incoming=True, evicted_bundle=None)

        active_priorities = [prio for prio, q in current_queues.items() if q]
        if not active_priorities:
            # Defensive fallback
            return DropDecision(admit_incoming=True, evicted_bundle=None)

        lowest_prio = min(active_priorities)

        if incoming_bundle.priority > lowest_prio:
            evicted_bundle = current_queues[lowest_prio].popleft()
            return DropDecision(admit_incoming=True, evicted_bundle=evicted_bundle)

        return DropDecision(admit_incoming=False, evicted_bundle=None)