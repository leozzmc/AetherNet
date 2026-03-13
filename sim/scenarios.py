from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class ScenarioProfile:
    name: str
    description: str
    duration_sec: int
    contacts: List[Dict[str, Any]]
    inject_short_lived_bundle: bool = False

    def generate_plan(self) -> Dict[str, Any]:
        return {
            "simulation_duration_sec": self.duration_sec,
            "contacts": self.contacts,
        }


_SCENARIOS: Dict[str, ScenarioProfile] = {}


def register_scenario(profile: ScenarioProfile) -> None:
    _SCENARIOS[profile.name] = profile


def list_scenarios() -> List[str]:
    return sorted(_SCENARIOS.keys())


def get_scenario(name: str) -> ScenarioProfile:
    if name not in _SCENARIOS:
        raise ValueError(f"Scenario '{name}' not found. Available: {list_scenarios()}")
    return _SCENARIOS[name]


register_scenario(
    ScenarioProfile(
        name="default_multihop",
        description="Normal MVP flow: lunar -> relay -> ground allows successful end-to-end delivery.",
        duration_sec=30,
        inject_short_lived_bundle=False,
        contacts=[
            {
                "source": "lunar-node",
                "target": "leo-relay",
                "start_time": 5,
                "end_time": 10,
                "one_way_delay_ms": 100,
                "bandwidth_kbit": 256,
                "bidirectional": False,
            },
            {
                "source": "leo-relay",
                "target": "ground-station",
                "start_time": 15,
                "end_time": 25,
                "one_way_delay_ms": 40,
                "bandwidth_kbit": 2048,
                "bidirectional": False,
            },
        ],
    )
)

register_scenario(
    ScenarioProfile(
        name="delayed_delivery",
        description="Second hop opens much later. Demonstrates longer waiting in relay storage.",
        duration_sec=60,
        inject_short_lived_bundle=False,
        contacts=[
            {
                "source": "lunar-node",
                "target": "leo-relay",
                "start_time": 5,
                "end_time": 10,
                "one_way_delay_ms": 100,
                "bandwidth_kbit": 256,
                "bidirectional": False,
            },
            {
                "source": "leo-relay",
                "target": "ground-station",
                "start_time": 45,
                "end_time": 55,
                "one_way_delay_ms": 40,
                "bandwidth_kbit": 2048,
                "bidirectional": False,
            },
        ],
    )
)

register_scenario(
    ScenarioProfile(
        name="expiry_before_contact",
        description="Contact opens too late for a short-lived telemetry bundle. Demonstrates expiry and purge behavior.",
        duration_sec=30,
        inject_short_lived_bundle=True,
        contacts=[
            {
                "source": "lunar-node",
                "target": "leo-relay",
                "start_time": 20,
                "end_time": 25,
                "one_way_delay_ms": 100,
                "bandwidth_kbit": 256,
                "bidirectional": False,
            }
        ],
    )
)