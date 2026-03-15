import json

from link.link_model import LinkModel
from router.contact_manager import ContactManager


def test_contact_manager_get_link_models(tmp_path):
    plan = {
        "simulation_duration_sec": 30,
        "contacts": [
            {
                "source": "lunar-node",
                "target": "leo-relay",
                "start_time": 5,
                "end_time": 10,
                "one_way_delay_ms": 1500,
                "bandwidth_kbit": 256,
                "loss_percent": 0.0,
                "bidirectional": False,
                "description": "Lunar uplink",
            }
        ],
    }

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    manager = ContactManager(str(plan_path))
    links = manager.get_link_models()

    assert len(links) == 1
    assert isinstance(links[0], LinkModel)
    assert links[0].source == "lunar-node"
    assert links[0].target == "leo-relay"
    assert links[0].start_time == 5
    assert links[0].end_time == 10


def test_contact_manager_get_active_link_models(tmp_path):
    plan = {
        "simulation_duration_sec": 30,
        "contacts": [
            {
                "source": "lunar-node",
                "target": "leo-relay",
                "start_time": 5,
                "end_time": 10,
                "one_way_delay_ms": 1500,
                "bandwidth_kbit": 256,
            }
        ],
    }

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    manager = ContactManager(str(plan_path))

    assert manager.get_active_link_models(4) == []

    active = manager.get_active_link_models(5)
    assert len(active) == 1
    assert active[0].source == "lunar-node"
    assert active[0].target == "leo-relay"