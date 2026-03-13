import json
import tempfile

from router.contact_manager import ContactManager


def test_contact_manager_forwarding_directional():
    plan = {
        "simulation_duration_sec": 100,
        "contacts": [
            {
                "source": "moon",
                "target": "relay",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": False
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
        json.dump(plan, f)
        tmp_path = f.name

    cm = ContactManager(tmp_path)

    assert cm.is_forwarding_allowed("moon", "relay", 5) is False
    assert cm.is_forwarding_allowed("moon", "relay", 15) is True
    assert cm.is_forwarding_allowed("relay", "moon", 15) is False
    assert cm.is_forwarding_allowed("moon", "relay", 25) is False


def test_contact_manager_forwarding_bidirectional():
    plan = {
        "simulation_duration_sec": 100,
        "contacts": [
            {
                "source": "moon",
                "target": "relay",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": True
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
        json.dump(plan, f)
        tmp_path = f.name

    cm = ContactManager(tmp_path)

    assert cm.is_forwarding_allowed("moon", "relay", 15) is True
    assert cm.is_forwarding_allowed("relay", "moon", 15) is True


def test_get_active_contacts():
    plan = {
        "simulation_duration_sec": 100,
        "contacts": [
            {
                "source": "moon",
                "target": "relay",
                "start_time": 10,
                "end_time": 20,
                "one_way_delay_ms": 1000,
                "bandwidth_kbit": 100,
                "bidirectional": False
            },
            {
                "source": "relay",
                "target": "earth",
                "start_time": 15,
                "end_time": 30,
                "one_way_delay_ms": 40,
                "bandwidth_kbit": 1000,
                "bidirectional": False
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
        json.dump(plan, f)
        tmp_path = f.name

    cm = ContactManager(tmp_path)
    active = cm.get_active_contacts(16)

    assert len(active) == 2
    assert {f"{c.source}->{c.target}" for c in active} == {"moon->relay", "relay->earth"}