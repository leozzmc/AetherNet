import json
from pathlib import Path
from typing import Any, Dict, List

from router.contact_manager import Contact


def parse_contact_plan(data: Dict[str, Any]) -> List[Contact]:
    """
    Wave-28: Deterministic contact plan parser.

    Validate and convert a JSON-compatible dictionary into a sorted list
    of Contact objects. This lays the groundwork for data-driven scenario
    inputs without modifying simulator runtime behavior.
    """
    if not isinstance(data, dict):
        raise ValueError("Input data must be a dictionary.")

    if "contacts" not in data:
        raise ValueError("Missing required key: 'contacts'.")

    contacts_raw = data["contacts"]
    if not isinstance(contacts_raw, list):
        raise ValueError("The 'contacts' key must contain a list.")

    parsed_contacts: List[Contact] = []
    required_fields = [
        "source",
        "target",
        "start_time",
        "end_time",
        "one_way_delay_ms",
        "bandwidth_kbit",
    ]

    for idx, raw in enumerate(contacts_raw):
        if not isinstance(raw, dict):
            raise ValueError(f"Contact at index {idx} must be a dictionary.")

        for field in required_fields:
            if field not in raw:
                raise ValueError(f"Contact at index {idx} is missing required field: '{field}'")

        source = raw["source"]
        target = raw["target"]
        start_time = raw["start_time"]
        end_time = raw["end_time"]
        one_way_delay_ms = raw["one_way_delay_ms"]
        bandwidth_kbit = raw["bandwidth_kbit"]

        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"Contact at index {idx}: 'source' must be a non-empty string.")

        if not isinstance(target, str) or not target.strip():
            raise ValueError(f"Contact at index {idx}: 'target' must be a non-empty string.")

        if not isinstance(start_time, (int, float)) or not isinstance(end_time, (int, float)):
            raise ValueError(f"Contact at index {idx}: start_time and end_time must be numeric.")

        if end_time <= start_time:
            raise ValueError(f"Contact at index {idx}: end_time must be strictly greater than start_time.")

        if not isinstance(one_way_delay_ms, (int, float)) or one_way_delay_ms < 0:
            raise ValueError(f"Contact at index {idx}: one_way_delay_ms must be >= 0.")

        if not isinstance(bandwidth_kbit, (int, float)) or bandwidth_kbit <= 0:
            raise ValueError(f"Contact at index {idx}: bandwidth_kbit must be > 0.")

        contact = Contact(
            source=source.strip(),
            target=target.strip(),
            start_time=start_time,
            end_time=end_time,
            one_way_delay_ms=one_way_delay_ms,
            bandwidth_kbit=bandwidth_kbit,
        )
        parsed_contacts.append(contact)

    parsed_contacts.sort(key=lambda c: (c.start_time, c.source, c.target))
    return parsed_contacts


def load_contact_plan_from_json(path: str) -> List[Contact]:
    """
    Read a JSON file from disk and parse it into Contact objects.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Contact plan file not found: {path}")

    with file_path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in file {path}: {e}")

    return parse_contact_plan(data)