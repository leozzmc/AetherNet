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

    def _discard_expired_heads(self, current_time: int) -> None:
        """
        Remove expired bundles only from queue heads, matching the same traversal
        semantics used by dequeue/peek.
        """
        for prio in sorted(self.queues.keys(), reverse=True):
            q = self.queues[prio]
            while q and q[0].is_expired(current_time):
                expired = q.popleft()
                expired.transition(BundleStatus.EXPIRED)

    def peek(self, current_time: int) -> Optional[Bundle]:
        """
        Return the highest-priority non-expired bundle without removing it.

        Expired bundles at queue heads are marked EXPIRED and discarded so that
        peek() and dequeue() observe the same effective queue semantics.
        """
        self._discard_expired_heads(current_time)

        for prio in sorted(self.queues.keys(), reverse=True):
            q = self.queues[prio]
            if q:
                return q[0]

        return None

    def dequeue(self, current_time: int) -> Optional[Bundle]:
        """
        Return the highest-priority non-expired bundle.
        Expired bundles are marked EXPIRED and discarded.
        """
        self._discard_expired_heads(current_time)

        for prio in sorted(self.queues.keys(), reverse=True):
            q = self.queues[prio]
            if q:
                return q.popleft()

        return None

    def size(self) -> int:
        return sum(len(q) for q in self.queues.values())

    def is_empty(self) -> bool:
        return self.size() == 0