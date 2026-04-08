import pytest

from aether_demo import Phase6ScenarioRegistry
from aether_scenarios import ScenarioGenerator


def test_scenario_names_are_registered_and_loadable():
    expected_names = {
        "clean_baseline_phase6",
        "degraded_network_phase6",
        "jammed_link_phase6",
        "mixed_risk_phase6",
    }

    registered_names = set(Phase6ScenarioRegistry.get_all_scenario_names())
    assert registered_names == expected_names

    for name in expected_names:
        spec = Phase6ScenarioRegistry.get_spec_by_name(name)
        assert spec.scenario_name == name


def test_invalid_scenario_name_raises_error():
    with pytest.raises(ValueError, match="Unknown Phase-6 scenario name"):
        Phase6ScenarioRegistry.get_spec_by_name("non_existent_scenario")


def test_scenario_generation_is_deterministic():
    generator = ScenarioGenerator()

    spec1 = Phase6ScenarioRegistry.get_mixed_risk()
    spec2 = Phase6ScenarioRegistry.get_mixed_risk()

    scenario1 = generator.generate(spec1)
    scenario2 = generator.generate(spec2)

    assert scenario1.to_dict() == scenario2.to_dict()


def test_clean_baseline_configuration():
    spec = Phase6ScenarioRegistry.get_clean_baseline()
    assert spec.include_reliability_trace is False
    assert spec.include_adversarial_trace is False


def test_degraded_network_configuration():
    spec = Phase6ScenarioRegistry.get_degraded_network()
    assert spec.include_reliability_trace is True
    assert spec.include_adversarial_trace is False
    assert spec.loss_probability > 0
    assert spec.max_extra_delay_ms > 0


def test_jammed_link_configuration():
    spec = Phase6ScenarioRegistry.get_jammed_link()
    assert spec.include_reliability_trace is False
    assert spec.include_adversarial_trace is True
    assert spec.jamming_probability > 0
    assert spec.malicious_drop_probability > 0


def test_mixed_risk_configuration():
    spec = Phase6ScenarioRegistry.get_mixed_risk()
    assert spec.include_reliability_trace is True
    assert spec.include_adversarial_trace is True
    assert spec.loss_probability > 0
    assert spec.jamming_probability > 0