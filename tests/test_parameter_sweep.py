import pytest

from sim.experiment_harness import ExperimentCase, ExperimentHarness
from sim.parameter_sweep import build_parameter_sweep


def test_single_parameter_sweep():
    cases = build_parameter_sweep(
        profile_name="minimal_baseline",
        sweep_spec={"tick_size": [1, 5]},
    )

    assert len(cases) == 2
    assert all(isinstance(case, ExperimentCase) for case in cases)

    assert cases[0].case_name == "minimal_baseline__default_multihop__tick_size1"
    assert cases[0].tick_size == 1

    assert cases[1].case_name == "minimal_baseline__default_multihop__tick_size5"
    assert cases[1].tick_size == 5


def test_two_parameter_cartesian_expansion():
    cases = build_parameter_sweep(
        profile_name="routing_baseline",
        sweep_spec={
            "max_steps": [50, 100],
            "tick_size": [1, 2],
        },
    )

    assert len(cases) == 8

    first_base_name = "routing_baseline__default_multihop__tick1"
    assert cases[0].case_name == f"{first_base_name}__max_steps50__tick_size1"
    assert cases[1].case_name == f"{first_base_name}__max_steps50__tick_size2"
    assert cases[2].case_name == f"{first_base_name}__max_steps100__tick_size1"
    assert cases[3].case_name == f"{first_base_name}__max_steps100__tick_size2"

    assert cases[0].simulation_end_override == 50
    assert cases[0].tick_size == 1
    assert cases[3].simulation_end_override == 100
    assert cases[3].tick_size == 2


def test_unsupported_parameter_raises():
    with pytest.raises(ValueError) as excinfo:
        build_parameter_sweep(
            "minimal_baseline",
            {"magic_param": [1, 2]},
        )

    assert "Unsupported sweep parameter: 'magic_param'" in str(excinfo.value)


def test_invalid_values_raise():
    with pytest.raises(ValueError) as excinfo:
        build_parameter_sweep("minimal_baseline", {})
    assert "sweep_spec cannot be empty." in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        build_parameter_sweep("minimal_baseline", {"tick_size": []})
    assert "Parameter 'tick_size' cannot be an empty list." in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        build_parameter_sweep("minimal_baseline", {"tick_size": [0]})
    assert "Parameter 'tick_size' values must be positive integers." in str(
        excinfo.value
    )

    with pytest.raises(ValueError) as excinfo:
        build_parameter_sweep("minimal_baseline", {"tick_size": [-1]})
    assert "Parameter 'tick_size' values must be positive integers." in str(
        excinfo.value
    )

    with pytest.raises(ValueError) as excinfo:
        build_parameter_sweep("minimal_baseline", {"tick_size": [1.5]})
    assert "Parameter 'tick_size' values must be strict integers." in str(
        excinfo.value
    )

    with pytest.raises(ValueError) as excinfo:
        build_parameter_sweep("minimal_baseline", {"tick_size": [True]})
    assert "Parameter 'tick_size' values must be strict integers." in str(
        excinfo.value
    )


def test_duplicate_values_raise():
    with pytest.raises(ValueError) as excinfo:
        build_parameter_sweep(
            "minimal_baseline",
            {"tick_size": [1, 1, 5]},
        )

    assert "Parameter 'tick_size' contains duplicate value: 1" in str(excinfo.value)


def test_repeated_calls_are_identical():
    spec = {"max_steps": [100, 50]}

    cases_1 = build_parameter_sweep("minimal_baseline", spec)
    cases_2 = build_parameter_sweep("minimal_baseline", spec)

    assert [case.case_name for case in cases_1] == [
        case.case_name for case in cases_2
    ]
    assert [case.simulation_end_override for case in cases_1] == [
        case.simulation_end_override for case in cases_2
    ]

    assert cases_1[0].case_name == "minimal_baseline__default_multihop__max_steps50"
    assert cases_1[1].case_name == "minimal_baseline__default_multihop__max_steps100"


def test_integration_with_experiment_harness():
    cases = build_parameter_sweep(
        profile_name="minimal_baseline",
        sweep_spec={"max_steps": [3, 5]},
    )

    results = ExperimentHarness.run_experiments(cases)

    assert len(results) == 2
    assert results[0].case_name == "minimal_baseline__default_multihop__max_steps3"
    assert results[1].case_name == "minimal_baseline__default_multihop__max_steps5"

    assert hasattr(results[0], "delivery_ratio")
    assert hasattr(results[1], "delivery_ratio")