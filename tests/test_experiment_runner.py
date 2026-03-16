import pytest

from sim.experiment_runner import ExperimentSpec, run_experiment, run_experiments


def test_spec_valid():
    spec = ExperimentSpec(name="exp1", scenario_name="default_multihop")
    assert spec.name == "exp1"
    assert spec.scenario_name == "default_multihop"
    assert spec.tick_size == 1
    assert spec.end_time_override is None


def test_spec_empty_name_raises():
    with pytest.raises(ValueError, match="Experiment name must not be empty"):
        ExperimentSpec(name="", scenario_name="default_multihop")


def test_spec_empty_scenario_name_raises():
    with pytest.raises(ValueError, match="Scenario name must not be empty"):
        ExperimentSpec(name="exp1", scenario_name="   ")


def test_spec_invalid_tick_size_raises():
    with pytest.raises(ValueError, match="tick_size must be strictly positive"):
        ExperimentSpec(name="exp1", scenario_name="default_multihop", tick_size=0)


def test_spec_invalid_end_time_override_raises():
    with pytest.raises(ValueError, match="end_time_override must be strictly positive"):
        ExperimentSpec(name="exp1", scenario_name="default_multihop", end_time_override=-5)


def test_run_single_experiment():
    spec = ExperimentSpec(
        name="test_single_exp",
        scenario_name="default_multihop",
        tick_size=1,
        end_time_override=50,
    )

    result = run_experiment(spec)

    assert result["experiment_name"] == "test_single_exp"
    assert result["scenario_name"] == "default_multihop"
    assert result["tick_size"] == 1
    assert result["end_time_override"] == 50

    assert "report" in result
    assert "summary" in result
    assert result["report"]["scenario_name"] == "default_multihop"
    assert "final_metrics" in result["report"]


def test_run_experiments_duplicate_names_raises():
    spec1 = ExperimentSpec(name="dup_exp", scenario_name="default_multihop")
    spec2 = ExperimentSpec(name="dup_exp", scenario_name="delayed_delivery")

    with pytest.raises(ValueError, match="Duplicate experiment name detected: 'dup_exp'"):
        run_experiments([spec1, spec2])


def test_run_multiple_experiments():
    spec1 = ExperimentSpec(name="exp_baseline", scenario_name="default_multihop", end_time_override=20)
    spec2 = ExperimentSpec(name="exp_faster_ticks", scenario_name="default_multihop", tick_size=2, end_time_override=20)

    batch_result = run_experiments([spec1, spec2])

    assert batch_result["experiment_names"] == ["exp_baseline", "exp_faster_ticks"]
    assert len(batch_result["results"]) == 2

    assert batch_result["results"][0]["experiment_name"] == "exp_baseline"
    assert batch_result["results"][0]["tick_size"] == 1
    assert batch_result["results"][1]["experiment_name"] == "exp_faster_ticks"
    assert batch_result["results"][1]["tick_size"] == 2

    assert "aggregate_comparison" in batch_result
    agg = batch_result["aggregate_comparison"]
    assert "aggregate" in agg
    assert "per_scenario_summaries" in agg
    assert len(agg["per_scenario_summaries"]) == 2


def test_run_experiments_empty_list_returns_stable_structure():
    batch_result = run_experiments([])

    assert batch_result["experiment_names"] == []
    assert batch_result["results"] == []

    agg = batch_result["aggregate_comparison"]
    assert "aggregate" in agg
    assert "per_scenario_summaries" in agg
    assert agg["per_scenario_summaries"] == []