import pytest
from sim.scenarios import list_scenarios, get_scenario, ScenarioProfile


def test_scenario_registry_contains_defaults():
    scenarios = list_scenarios()
    assert "default_multihop" in scenarios
    assert "delayed_delivery" in scenarios
    assert "expiry_before_contact" in scenarios
    assert "multipath_competition" in scenarios
    assert "contact_timing_tradeoff" in scenarios


def test_get_valid_scenario():
    profile = get_scenario("default_multihop")
    assert isinstance(profile, ScenarioProfile)
    assert profile.name == "default_multihop"

    plan = profile.generate_plan()
    assert "simulation_duration_sec" in plan
    assert "contacts" in plan
    assert "routing_mode" in plan
    assert len(plan["contacts"]) > 0


def test_get_invalid_scenario():
    with pytest.raises(ValueError, match="not found"):
        get_scenario("non_existent_mars_scenario")


def test_scenario_plan_includes_default_routing_mode():
    profile = get_scenario("default_multihop")
    plan = profile.generate_plan()
    assert profile.routing_mode == "baseline"
    assert plan["routing_mode"] == "baseline"


def test_multipath_competition_contains_parallel_relays():
    profile = get_scenario("multipath_competition")
    contacts = profile.generate_plan()["contacts"]
    assert any(c["target"] == "relay-a" for c in contacts)
    assert any(c["target"] == "relay-b" for c in contacts)


def test_contact_timing_tradeoff_contains_early_and_late_relays():
    profile = get_scenario("contact_timing_tradeoff")
    contacts = profile.generate_plan()["contacts"]
    relay_a = [c for c in contacts if c["target"] == "relay-a"]
    relay_b = [c for c in contacts if c["target"] == "relay-b"]
    assert relay_a and relay_b
    assert relay_a[0]["start_time"] > relay_b[0]["start_time"]
