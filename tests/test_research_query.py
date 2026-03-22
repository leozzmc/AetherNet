import json
from pathlib import Path

import pytest

from sim.experiment_artifacts import write_artifact_bundle
from sim.experiment_harness import ExperimentHarness
from sim.parameter_sweep import build_parameter_sweep
from sim.research_query import (
    find_cases_by_scenario,
    get_best_case_by_metric,
    get_case_batches,
    load_research_aggregation,
    rank_cases_by_metric,
)
from sim.sweep_aggregation import write_sweep_aggregation


def create_mock_aggregation_json(path: Path, overrides: dict | None = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    data = {
        "type": "sweep_aggregation",
        "version": "1.0",
        "root_path": "/mock/root",
        "artifact_count": 1,
        "case_count": 2,
        "cases": [
            {
                "case_name": "case_alpha",
                "research_note": "keep_me",
                "batches": [
                    {
                        "artifact_dir_name": "b1",
                        "batch_label": "lbl1",
                        "scenario_name": "scenario_X",
                        "delivery_ratio": 0.5,
                        "unique_delivered": 10,
                        "duplicate_deliveries": 0,
                        "store_remaining": 5,
                    }
                ],
            },
            {
                "case_name": "case_beta",
                "batches": [
                    {
                        "artifact_dir_name": "b2",
                        "batch_label": "lbl2",
                        "scenario_name": "scenario_Y",
                        "delivery_ratio": 0.9,
                        "unique_delivered": 20,
                        "duplicate_deliveries": 1,
                        "store_remaining": 2,
                    }
                ],
            },
        ],
    }
    if overrides:
        data.update(overrides)

    json_path = path / "sweep_aggregation.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_integration_with_real_pipeline(tmp_path):
    """Wave-66: Real pipeline integration test."""
    sweep_cases = build_parameter_sweep("minimal_baseline", {"tick_size": [1, 2]})
    results = ExperimentHarness.run_experiments(sweep_cases)

    artifacts_dir = tmp_path / "artifacts"
    write_artifact_bundle(results, str(artifacts_dir / "batch_1"), batch_label="run_1")
    write_artifact_bundle(results, str(artifacts_dir / "batch_2"), batch_label="run_2")

    agg_dir = tmp_path / "aggregation"
    write_sweep_aggregation(str(artifacts_dir), str(agg_dir))
    agg_json_path = agg_dir / "sweep_aggregation.json"

    agg_data = load_research_aggregation(str(agg_json_path))
    assert agg_data["case_count"] == 2

    matched = find_cases_by_scenario(agg_data, "default_multihop")
    assert len(matched) == 2

    best = get_best_case_by_metric(agg_data, "delivery_ratio", aggregate="mean")
    assert best["metric_name"] == "delivery_ratio"
    assert "case_name" in best


def test_load_preserves_case_level_fields(tmp_path):
    json_path = create_mock_aggregation_json(tmp_path)
    agg_data = load_research_aggregation(str(json_path))

    assert agg_data["cases"][0]["case_name"] == "case_alpha"
    assert agg_data["cases"][0]["research_note"] == "keep_me"


def test_find_cases_by_scenario(tmp_path):
    json_path = create_mock_aggregation_json(tmp_path)
    agg_data = load_research_aggregation(str(json_path))

    cases_x = find_cases_by_scenario(agg_data, "scenario_X")
    assert len(cases_x) == 1
    assert cases_x[0]["case_name"] == "case_alpha"

    cases_z = find_cases_by_scenario(agg_data, "scenario_Z")
    assert len(cases_z) == 0


def test_get_case_batches(tmp_path):
    json_path = create_mock_aggregation_json(tmp_path)
    agg_data = load_research_aggregation(str(json_path))

    batches = get_case_batches(agg_data, "case_beta")
    assert len(batches) == 1
    assert batches[0]["scenario_name"] == "scenario_Y"

    with pytest.raises(ValueError) as excinfo:
        get_case_batches(agg_data, "case_ghost")
    assert "not found in aggregation data" in str(excinfo.value)


def test_rank_cases_by_metric_mean(tmp_path):
    json_path = create_mock_aggregation_json(tmp_path)
    agg_data = load_research_aggregation(str(json_path))

    ranked = rank_cases_by_metric(agg_data, "delivery_ratio", aggregate="mean")

    assert len(ranked) == 2
    assert ranked[0]["case_name"] == "case_beta"
    assert ranked[1]["case_name"] == "case_alpha"
    assert ranked[0]["metric_value"] == 0.9
    assert ranked[0]["batch_count"] == 1


def test_tie_breaking_is_deterministic(tmp_path):
    json_path = create_mock_aggregation_json(tmp_path)
    content = json.loads(json_path.read_text(encoding="utf-8"))
    content["cases"][1]["batches"][0]["delivery_ratio"] = 0.5
    json_path.write_text(json.dumps(content), encoding="utf-8")

    agg_data = load_research_aggregation(str(json_path))

    ranked_desc = rank_cases_by_metric(agg_data, "delivery_ratio", descending=True)
    assert ranked_desc[0]["case_name"] == "case_alpha"
    assert ranked_desc[1]["case_name"] == "case_beta"

    ranked_asc = rank_cases_by_metric(agg_data, "delivery_ratio", descending=False)
    assert ranked_asc[0]["case_name"] == "case_alpha"
    assert ranked_asc[1]["case_name"] == "case_beta"


def test_get_best_case_uses_metric_specific_direction(tmp_path):
    json_path = create_mock_aggregation_json(tmp_path)
    agg_data = load_research_aggregation(str(json_path))

    best_delivery = get_best_case_by_metric(agg_data, "delivery_ratio", aggregate="mean")
    assert best_delivery["case_name"] == "case_beta"

    best_duplicates = get_best_case_by_metric(
        agg_data,
        "duplicate_deliveries",
        aggregate="mean",
    )
    assert best_duplicates["case_name"] == "case_alpha"


def test_unsupported_metric_aggregate_and_top_n_raise(tmp_path):
    json_path = create_mock_aggregation_json(tmp_path)
    agg_data = load_research_aggregation(str(json_path))

    with pytest.raises(ValueError) as excinfo1:
        rank_cases_by_metric(agg_data, "magic_metric")
    assert "Unsupported metric" in str(excinfo1.value)

    with pytest.raises(ValueError) as excinfo2:
        rank_cases_by_metric(agg_data, "delivery_ratio", aggregate="median")
    assert "Unsupported aggregate mode" in str(excinfo2.value)

    with pytest.raises(ValueError) as excinfo3:
        rank_cases_by_metric(agg_data, "delivery_ratio", top_n=0)
    assert "top_n must be a positive integer or None." in str(excinfo3.value)


def test_optional_metric_exclusion(tmp_path):
    """Ensure cases without valid optional metric data are safely excluded from ranking."""
    json_path = create_mock_aggregation_json(tmp_path)
    content = json.loads(json_path.read_text(encoding="utf-8"))

    content["cases"][0]["batches"][0]["bundles_dropped_total"] = {}
    content["cases"][1]["batches"][0]["bundles_dropped_total"] = 5
    json_path.write_text(json.dumps(content), encoding="utf-8")

    agg_data = load_research_aggregation(str(json_path))

    ranked = rank_cases_by_metric(agg_data, "bundles_dropped_total")

    assert len(ranked) == 1
    assert ranked[0]["case_name"] == "case_beta"
    assert ranked[0]["metric_value"] == 5.0