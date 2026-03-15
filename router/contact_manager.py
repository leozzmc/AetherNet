import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from link.link_model import LinkModel


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
    capacity_bundles: int | None = None

    def is_active(self, current_time: int) -> bool:
        return self.start_time <= current_time < self.end_time

    def allows(self, source: str, target: str) -> bool:
        if self.source == source and self.target == target:
            return True
        if self.bidirectional and self.source == target and self.target == source:
            return True
        return False

    def to_link_model(self) -> LinkModel:
        return LinkModel(
            source=self.source,
            target=self.target,
            start_time=self.start_time,
            end_time=self.end_time,
            one_way_delay_ms=self.one_way_delay_ms,
            bandwidth_kbit=self.bandwidth_kbit,
            loss_percent=self.loss_percent,
            bidirectional=self.bidirectional,
            description=self.description,
        )


class ContactManager:
    """Loads and queries a static contact plan for application-layer forwarding decisions."""

    def __init__(self, plan_path: str) -> None:
        self.plan_path = Path(plan_path)
        with self.plan_path.open("r", encoding="utf-8") as f:
            raw_plan = json.load(f)

        self.simulation_duration_sec = raw_plan["simulation_duration_sec"]
        self.contacts: List[Contact] = [self._parse_contact(c) for c in raw_plan.get("contacts", [])]

    def _parse_contact(self, raw: dict[str, Any]) -> Contact:
        capacity_bundles = raw.get("capacity_bundles")
        if capacity_bundles is not None and capacity_bundles < 0:
            raise ValueError(f"capacity_bundles must be >= 0, got {capacity_bundles}")

        contact = Contact(
            source=raw["source"],
            target=raw["target"],
            start_time=raw["start_time"],
            end_time=raw["end_time"],
            # Backward-compatible defaults for simpler plans/tests
            one_way_delay_ms=raw.get("one_way_delay_ms", 0),
            bandwidth_kbit=raw.get("bandwidth_kbit", 0),
            loss_percent=raw.get("loss_percent", 0.0),
            bidirectional=raw.get("bidirectional", False),
            description=raw.get("description", ""),
            capacity_bundles=capacity_bundles,
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

    def get_link_models(self) -> List[LinkModel]:
        return [contact.to_link_model() for contact in self.contacts]

    def get_active_link_models(self, current_time: int) -> List[LinkModel]:
        return [contact.to_link_model() for contact in self.get_active_contacts(current_time)]