from collections import deque
from typing import Optional, Dict

from router.bundle import Bundle, BundleStatus


class StrictPriorityQueue:
    """
    Deterministic strict-priority queue with FIFO ordering within each priority class.
    Higher integer priority is dequeued first.

    Important design note:
    Queue membership does NOT define the bundle lifecycle state.
    A bundle may be STORED and still be present in an outbound queue awaiting
    a future forwarding opportunity.
    """

    def __init__(self) -> None:
        self.queues: Dict[int, deque[Bundle]] = {}

    def enqueue(self, bundle: Bundle) -> None:
        prio = bundle.priority
        if prio not in self.queues:
            self.queues[prio] = deque()
        self.queues[prio].append(bundle)

    def dequeue(self, current_time: int) -> Optional[Bundle]:
        """
        Return the highest-priority non-expired bundle.
        Expired bundles are marked EXPIRED and discarded.
        """
        for prio in sorted(self.queues.keys(), reverse=True):
            q = self.queues[prio]
            while q:
                bundle = q.popleft()
                if bundle.is_expired(current_time):
                    bundle.transition(BundleStatus.EXPIRED)
                    continue
                return bundle

        return None

    def size(self) -> int:
        return sum(len(q) for q in self.queues.values())

    def is_empty(self) -> bool:
        return self.size() == 0