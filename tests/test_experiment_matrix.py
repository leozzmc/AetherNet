import pytest

from sim.experiment_harness import ExperimentHarness
from sim.experiment_matrix import ExperimentMatrix, ExperimentMatrixBuilder


def test_matrix_expansion_preserves_deterministic_order():
    matrix = ExperimentMatrix(
        scenario_names=["s1", "s2"],
        tick_sizes=[1, 5],
        simulation_end_overrides=[None],
    )

    cases = ExperimentMatrixBuilder.expand(matrix)

    assert len(cases) == 4

    assert cases[0].scenario_name == "s1"
    assert cases[0].tick_size == 1
    assert cases[0].simulation_end_override is None

    assert cases[1].scenario_name == "s1"
    assert cases[1].tick_size == 5
    assert cases[1].simulation_end_override is None

    assert cases[2].scenario_name == "s2"
    assert cases[2].tick_size == 1
    assert cases[2].simulation_end_override is None

    assert cases[3].scenario_name == "s2"
    assert cases[3].tick_size == 5
    assert cases[3].simulation_end_override is None


def test_generated_case_names_are_stable():
    matrix = ExperimentMatrix(
        scenario_names=["default_multihop"],
        tick_sizes=[1, 5],
        simulation_end_overrides=[100, None],
    )

    cases = ExperimentMatrixBuilder.expand(matrix)

    assert len(cases) == 4
    assert cases[0].case_name == "default_multihop__tick1__end100"
    assert cases[1].case_name == "default_multihop__tick1__enddefault"
    assert cases[2].case_name == "default_multihop__tick5__end100"
    assert cases[3].case_name == "default_multihop__tick5__enddefault"


def test_cartesian_expansion_count_is_correct():
    matrix = ExperimentMatrix(
        scenario_names=["s1", "s2", "s3"],
        tick_sizes=[1, 2],
        simulation_end_overrides=[None, 20],
    )

    cases = ExperimentMatrixBuilder.expand(matrix)

    # 3 * 2 * 2 = 12
    assert len(cases) == 12


def test_invalid_empty_scenario_list_raises():
    with pytest.raises(ValueError) as excinfo:
        ExperimentMatrix(scenario_names=[])

    assert "at least one scenario name" in str(excinfo.value)


def test_invalid_tick_sizes_raise():
    with pytest.raises(ValueError) as excinfo:
        ExperimentMatrix(scenario_names=["default_multihop"], tick_sizes=[0])

    assert "Invalid tick size" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        ExperimentMatrix(scenario_names=["default_multihop"], tick_sizes=[1, -5])

    assert "Invalid tick size" in str(excinfo.value)


def test_generated_cases_can_run_through_experiment_harness():
    matrix = ExperimentMatrix(
        scenario_names=["default_multihop"],
        tick_sizes=[1],
        simulation_end_overrides=[5],
    )

    cases = ExperimentMatrixBuilder.expand(matrix)
    results = ExperimentHarness.run_experiments(cases)

    assert len(results) == 1
    assert results[0].case_name == "default_multihop__tick1__end5"
    assert results[0].scenario_name == "default_multihop"
    assert hasattr(results[0], "delivery_ratio")