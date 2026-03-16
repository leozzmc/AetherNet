import json
from pathlib import Path

import pytest

from sim.contact_plan_parser import load_contact_plan_from_json, parse_contact_plan


def test_parse_valid_in_memory_plan():
    data = {
        "contacts": [
            {
                "source": "lunar-node",
                "target": "leo-relay",
                "start_time": 0,
                "end_time": 10,
                "one_way_delay_ms": 1200,
                "bandwidth_kbit": 64,
            }
        ]
    }

    contacts = parse_contact_plan(data)
    assert len(contacts) == 1

    contact = contacts[0]
    assert contact.source == "lunar-node"
    assert contact.target == "leo-relay"
    assert contact.start_time == 0
    assert contact.end_time == 10
    assert contact.one_way_delay_ms == 1200
    assert contact.bandwidth_kbit == 64


def test_load_valid_contact_plan_from_json_file(tmp_path):
    data = {
        "contacts": [
            {
                "source": "relay-a",
                "target": "relay-b",
                "start_time": 15,
                "end_time": 30,
                "one_way_delay_ms": 400,
                "bandwidth_kbit": 256,
            }
        ]
    }

    file_path = tmp_path / "contact_plan.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")

    contacts = load_contact_plan_from_json(str(file_path))
    assert len(contacts) == 1
    assert contacts[0].source == "relay-a"


def test_missing_contacts_key_raises():
    with pytest.raises(ValueError, match="Missing required key: 'contacts'"):
        parse_contact_plan({"wrong_key": []})


def test_non_list_contacts_raises():
    with pytest.raises(ValueError, match="must contain a list"):
        parse_contact_plan({"contacts": {}})


def test_non_dict_contact_entry_raises():
    with pytest.raises(ValueError, match="must be a dictionary"):
        parse_contact_plan({"contacts": ["not-a-dict"]})


def test_missing_required_field_raises():
    data = {
        "contacts": [
            {
                "source": "node-a",
                "target": "node-b",
                "start_time": 0,
                "one_way_delay_ms": 100,
                "bandwidth_kbit": 50,
            }
        ]
    }

    with pytest.raises(ValueError, match="missing required field: 'end_time'"):
        parse_contact_plan(data)


def test_invalid_time_window_raises():
    data = {
        "contacts": [
            {
                "source": "a",
                "target": "b",
                "start_time": 10,
                "end_time": 10,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 10,
            }
        ]
    }

    with pytest.raises(ValueError, match="strictly greater than start_time"):
        parse_contact_plan(data)


def test_negative_delay_raises():
    data = {
        "contacts": [
            {
                "source": "a",
                "target": "b",
                "start_time": 0,
                "end_time": 5,
                "one_way_delay_ms": -50,
                "bandwidth_kbit": 10,
            }
        ]
    }

    with pytest.raises(ValueError, match="one_way_delay_ms must be >= 0"):
        parse_contact_plan(data)


def test_non_positive_bandwidth_raises():
    data = {
        "contacts": [
            {
                "source": "a",
                "target": "b",
                "start_time": 0,
                "end_time": 5,
                "one_way_delay_ms": 100,
                "bandwidth_kbit": 0,
            }
        ]
    }

    with pytest.raises(ValueError, match="bandwidth_kbit must be > 0"):
        parse_contact_plan(data)


def test_parser_returns_deterministic_sorting():
    data = {
        "contacts": [
            {
                "source": "b",
                "target": "c",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 1,
            },
            {
                "source": "a",
                "target": "b",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 1,
            },
            {
                "source": "a",
                "target": "c",
                "start_time": 5,
                "end_time": 10,
                "one_way_delay_ms": 0,
                "bandwidth_kbit": 1,
            },
        ]
    }

    contacts = parse_contact_plan(data)

    assert contacts[0].source == "a"
    assert contacts[0].target == "c"
    assert contacts[1].source == "a"
    assert contacts[1].target == "b"
    assert contacts[2].source == "b"
    assert contacts[2].target == "c"