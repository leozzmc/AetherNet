import pytest
from sim.scenarios import list_scenarios, get_scenario, ScenarioProfile

def test_scenario_registry_contains_defaults():
    scenarios = list_scenarios()
    assert "default_multihop" in scenarios
    assert "delayed_delivery" in scenarios
    assert "expiry_before_contact" in scenarios

def test_get_valid_scenario():
    profile = get_scenario("default_multihop")
    assert isinstance(profile, ScenarioProfile)
    assert profile.name == "default_multihop"
    
    plan = profile.generate_plan()
    assert "simulation_duration_sec" in plan
    assert "contacts" in plan
    assert len(plan["contacts"]) > 0

def test_get_invalid_scenario():
    with pytest.raises(ValueError, match="not found"):
        get_scenario("non_existent_mars_scenario")