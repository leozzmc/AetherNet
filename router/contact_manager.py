import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List


@dataclass(frozen=True)
class Contact:
    source: str
    target: str
    start_time: int
    end_time: int
    one_way_delay_ms: int
    bandwidth_kbit: int
    loss_percent: float = 0.0
    bidirectional: bool = False
    description: str = ""

    def is_active(self, current_time: int) -> bool:
        return self.start_time <= current_time < self.end_time

    def allows(self, source: str, target: str) -> bool:
        if self.source == source and self.target == target:
            return True
        if self.bidirectional and self.source == target and self.target == source:
            return True
        return False


class ContactManager:
    """Loads and queries a static contact plan for application-layer forwarding decisions."""

    def __init__(self, plan_path: str) -> None:
        self.plan_path = Path(plan_path)
        with self.plan_path.open("r", encoding="utf-8") as f:
            raw_plan = json.load(f)

        self.simulation_duration_sec = raw_plan["simulation_duration_sec"]
        self.contacts: List[Contact] = [self._parse_contact(c) for c in raw_plan.get("contacts", [])]

    def _parse_contact(self, raw: dict[str, Any]) -> Contact:
        contact = Contact(
            source=raw["source"],
            target=raw["target"],
            start_time=raw["start_time"],
            end_time=raw["end_time"],
            one_way_delay_ms=raw["one_way_delay_ms"],
            bandwidth_kbit=raw["bandwidth_kbit"],
            loss_percent=raw.get("loss_percent", 0.0),
            bidirectional=raw.get("bidirectional", False),
            description=raw.get("description", ""),
        )
        if contact.end_time <= contact.start_time:
            raise ValueError(
                f"Invalid contact window for {contact.source}->{contact.target}: "
                f"end_time must be greater than start_time."
            )
        return contact

    def get_active_contacts(self, current_time: int) -> List[Contact]:
        return [contact for contact in self.contacts if contact.is_active(current_time)]

    def is_forwarding_allowed(self, source: str, target: str, current_time: int) -> bool:
        return any(contact.is_active(current_time) and contact.allows(source, target) for contact in self.contacts)