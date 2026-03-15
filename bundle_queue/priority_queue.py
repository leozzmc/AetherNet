from collections import deque
from typing import Optional, Dict

from router.bundle import Bundle, BundleStatus
from router.congestion_control import DropLowestPriorityPolicy
from metrics.exporter import MetricsCollector


class StrictPriorityQueue:
    """
    Deterministic strict-priority queue with FIFO ordering within each priority class.
    Higher integer priority is dequeued first.

    Important design note:
    Queue membership does NOT define the bundle lifecycle state.
    A bundle may be STORED and still be present in an outbound queue awaiting
    a future forwarding opportunity.

    Wave-19:
    - optional queue size limit via max_size
    - deterministic congestion handling
    """

    def __init__(
        self,
        max_size: Optional[int] = None,
        congestion_policy=None,
        metrics: Optional[MetricsCollector] = None,
    ) -> None:
        self.queues: Dict[int, deque[Bundle]] = {}
        self.max_size = max_size
        self.congestion_policy = congestion_policy or DropLowestPriorityPolicy()
        self.metrics = metrics

    def enqueue(self, bundle: Bundle) -> bool:
        """
        Attempt to enqueue a bundle.

        Returns:
            True if the bundle was admitted.
            False if the incoming bundle was rejected due to congestion.
        """
        if self.max_size is not None and self.size() >= self.max_size:
            decision = self.congestion_policy.evaluate(
                incoming_bundle=bundle,
                current_queues=self.queues,
                current_size=self.size(),
                max_size=self.max_size,
            )

            if not decision.admit_incoming:
                if self.metrics is not None:
                    self.metrics.record_dropped(bundle.type, bundle.id)
                return False

            if decision.evicted_bundle is not None:
                if self.metrics is not None:
                    self.metrics.record_dropped(decision.evicted_bundle.type, decision.evicted_bundle.id)

        prio = bundle.priority
        if prio not in self.queues:
            self.queues[prio] = deque()
        self.queues[prio].append(bundle)
        return True

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