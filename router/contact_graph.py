from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from router.contact_manager import ContactManager


@dataclass(frozen=True)
class ContactOpportunity:
    """
    Wave-41: Represents a specific future communication opportunity.
    """

    source: str
    target: str
    start_time: int
    end_time: int
    estimated_arrival_time: int


class ContactForecast:
    """
    Minimal bounded future-contact helper for Wave-41 CGR-lite.

    This is intentionally NOT a full graph engine.
    It only helps reason about the next usable contact opportunity between two nodes.
    """

    def __init__(self, contact_manager: ContactManager):
        self.cm = contact_manager

    def find_next_contact(
        self,
        source: str,
        target: str,
        after_time: int,
    ) -> Optional[ContactOpportunity]:
        """
        Find the earliest contact opportunity from source to target that is
        still usable after `after_time`.

        If a contact is already open at `after_time`, it is considered usable
        immediately at `after_time`.
        """
        best_contact = None
        best_effective_start = None

        for contact in self.cm.contacts:
            if not contact.allows(source, target):
                continue

            if contact.end_time <= after_time:
                continue

            effective_start = max(after_time, contact.start_time)

            if best_effective_start is None or effective_start < best_effective_start:
                best_contact = contact
                best_effective_start = effective_start

        if best_contact is None or best_effective_start is None:
            return None

        transit_delay_sec = best_contact.one_way_delay_ms // 1000
        estimated_arrival_time = best_effective_start + transit_delay_sec

        return ContactOpportunity(
            source=source,
            target=target,
            start_time=best_effective_start,
            end_time=best_contact.end_time,
            estimated_arrival_time=estimated_arrival_time,
        )