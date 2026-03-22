import json
from pathlib import Path

import pytest

from sim.experiment_artifacts import write_artifact_bundle
from sim.experiment_harness import ExperimentHarness
from sim.parameter_sweep import build_parameter_sweep
from sim.research_table_export import export_research_tables
from sim.sweep_aggregation import write_sweep_aggregation


def create_mock_aggregation_json(path: Path, overrides: dict | None = None) -> Path:
    path.mkdir(parents=True, exist_ok=True)

    data = {
        "type": "sweep_aggregation",
        "version": "1.0",
        "root_path": "/mock/root",
        "artifact_count": 1,
        "case_count": 1,
        "cases": [
            {
                "case_name": "mock_case",
                "batches": [
                    {
                        "artifact_dir_name": "batch_1",
                        "batch_label": "lbl_1",
                        "scenario_name": "default_multihop",
                        "delivery_ratio": 0.5,
                        "unique_delivered": 10,
                        "duplicate_deliveries": 2,
                        "store_remaining": 5,
                        "bundles_dropped_total": 0,
                    }
                ],
            }
        ],
    }

    if overrides:
        data.update(overrides)

    json_path = path / "sweep_aggregation.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_export_from_valid_aggregation(tmp_path):
    json_path = create_mock_aggregation_json(tmp_path)
    out_dir = tmp_path / "export"

    export_research_tables(str(json_path), str(out_dir))

    assert (out_dir / "research_case_batch_table.csv").is_file()
    assert (out_dir / "research_case_summary_table.csv").is_file()


def test_invalid_aggregation_type_version_raises(tmp_path):
    json_path_1 = create_mock_aggregation_json(
        tmp_path / "t1",
        {"type": "wrong_type"},
    )
    with pytest.raises(ValueError) as excinfo_1:
        export_research_tables(str(json_path_1), str(tmp_path / "out1"))
    assert "type must be 'sweep_aggregation'" in str(excinfo_1.value)

    json_path_2 = create_mock_aggregation_json(
        tmp_path / "t2",
        {"version": "9.9"},
    )
    with pytest.raises(ValueError) as excinfo_2:
        export_research_tables(str(json_path_2), str(tmp_path / "out2"))
    assert "version must be '1.0'" in str(excinfo_2.value)


def test_case_count_mismatch_raises(tmp_path):
    json_path = create_mock_aggregation_json(
        tmp_path,
        {
            "case_count": 2,
        },
    )

    with pytest.raises(ValueError) as excinfo:
        export_research_tables(str(json_path), str(tmp_path / "out"))

    assert "'case_count' does not match the number of case entries" in str(excinfo.value)


def test_missing_metrics_raises(tmp_path):
    json_path = create_mock_aggregation_json(tmp_path)
    content = json.loads(json_path.read_text(encoding="utf-8"))

    del content["cases"][0]["batches"][0]["delivery_ratio"]
    json_path.write_text(json.dumps(content), encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        export_research_tables(str(json_path), str(tmp_path / "out"))

    assert "missing numeric metric 'delivery_ratio'" in str(excinfo.value)


def test_flat_batch_table_row_count(tmp_path):
    json_path = create_mock_aggregation_json(tmp_path)
    content = json.loads(json_path.read_text(encoding="utf-8"))

    content["cases"][0]["batches"].append(
        {
            "artifact_dir_name": "batch_2",
            "batch_label": "lbl_2",
            "scenario_name": "default_multihop",
            "delivery_ratio": 0.8,
            "unique_delivered": 15,
            "duplicate_deliveries": 1,
            "store_remaining": 2,
            "bundles_dropped_total": 0,
        }
    )
    json_path.write_text(json.dumps(content), encoding="utf-8")

    out_dir = tmp_path / "export"
    export_research_tables(str(json_path), str(out_dir))

    lines = (
        (out_dir / "research_case_batch_table.csv")
        .read_text(encoding="utf-8")
        .strip()
        .splitlines()
    )
    assert len(lines) == 3


def test_per_case_summary_table_correctness(tmp_path):
    json_path = create_mock_aggregation_json(tmp_path)
    content = json.loads(json_path.read_text(encoding="utf-8"))

    content["cases"][0]["batches"] = [
        {
            "artifact_dir_name": "b1",
            "batch_label": "l1",
            "scenario_name": "scenario_B",
            "delivery_ratio": 0.2,
            "unique_delivered": 10,
            "duplicate_deliveries": 0,
            "store_remaining": 0,
            "bundles_dropped_total": 0,
        },
        {
            "artifact_dir_name": "b2",
            "batch_label": "l2",
            "scenario_name": "scenario_A",
            "delivery_ratio": 0.8,
            "unique_delivered": 20,
            "duplicate_deliveries": 0,
            "store_remaining": 0,
            "bundles_dropped_total": 0,
        },
    ]
    json_path.write_text(json.dumps(content), encoding="utf-8")

    out_dir = tmp_path / "export"
    export_research_tables(str(json_path), str(out_dir))

    lines = (
        (out_dir / "research_case_summary_table.csv")
        .read_text(encoding="utf-8")
        .strip()
        .splitlines()
    )
    assert len(lines) == 2

    data_line = lines[1]
    assert "scenario_A;scenario_B" in data_line
    assert "mock_case,2," in data_line
    assert "0.200000,0.800000,0.500000" in data_line


def test_unsorted_input_still_exports_deterministically(tmp_path):
    json_path = create_mock_aggregation_json(
        tmp_path,
        {
            "case_count": 2,
            "cases": [
                {
                    "case_name": "case_b",
                    "batches": [
                        {
                            "artifact_dir_name": "batch_2",
                            "batch_label": "label_2",
                            "scenario_name": "scenario_B",
                            "delivery_ratio": 0.8,
                            "unique_delivered": 20,
                            "duplicate_deliveries": 1,
                            "store_remaining": 0,
                            "bundles_dropped_total": 0,
                        },
                        {
                            "artifact_dir_name": "batch_1",
                            "batch_label": "label_1",
                            "scenario_name": "scenario_A",
                            "delivery_ratio": 0.2,
                            "unique_delivered": 10,
                            "duplicate_deliveries": 0,
                            "store_remaining": 0,
                            "bundles_dropped_total": 0,
                        },
                    ],
                },
                {
                    "case_name": "case_a",
                    "batches": [
                        {
                            "artifact_dir_name": "batch_3",
                            "batch_label": "label_3",
                            "scenario_name": "scenario_C",
                            "delivery_ratio": 1.0,
                            "unique_delivered": 30,
                            "duplicate_deliveries": 0,
                            "store_remaining": 0,
                            "bundles_dropped_total": 0,
                        }
                    ],
                },
            ],
        },
    )

    out_dir = tmp_path / "export"
    export_research_tables(str(json_path), str(out_dir))

    batch_lines = (
        (out_dir / "research_case_batch_table.csv")
        .read_text(encoding="utf-8")
        .strip()
        .splitlines()
    )
    assert batch_lines[1].startswith("case_a,")
    assert batch_lines[2].startswith("case_b,batch_1,")
    assert batch_lines[3].startswith("case_b,batch_2,")


def test_deterministic_repeated_export(tmp_path):
    json_path = create_mock_aggregation_json(tmp_path)

    out_1 = tmp_path / "out1"
    out_2 = tmp_path / "out2"

    export_research_tables(str(json_path), str(out_1))
    export_research_tables(str(json_path), str(out_2))

    assert (out_1 / "research_case_batch_table.csv").read_text(encoding="utf-8") == (
        out_2 / "research_case_batch_table.csv"
    ).read_text(encoding="utf-8")
    assert (out_1 / "research_case_summary_table.csv").read_text(encoding="utf-8") == (
        out_2 / "research_case_summary_table.csv"
    ).read_text(encoding="utf-8")


def test_integration_with_real_pipeline(tmp_path):
    sweep_cases = build_parameter_sweep(
        "minimal_baseline",
        {"tick_size": [1, 2]},
    )

    results = ExperimentHarness.run_experiments(sweep_cases)

    artifacts_dir = tmp_path / "artifacts"
    write_artifact_bundle(
        results,
        str(artifacts_dir / "batch_1"),
        batch_label="run_1",
    )
    write_artifact_bundle(
        results,
        str(artifacts_dir / "batch_2"),
        batch_label="run_2",
    )

    aggregation_dir = tmp_path / "aggregation"
    write_sweep_aggregation(str(artifacts_dir), str(aggregation_dir))
    aggregation_json_path = aggregation_dir / "sweep_aggregation.json"

    export_dir = tmp_path / "research_tables"
    export_research_tables(str(aggregation_json_path), str(export_dir))

    batch_csv = export_dir / "research_case_batch_table.csv"
    summary_csv = export_dir / "research_case_summary_table.csv"

    assert batch_csv.is_file()
    assert summary_csv.is_file()

    summary_text = summary_csv.read_text(encoding="utf-8")
    assert "minimal_baseline__default_multihop__tick_size1" in summary_text
    assert "minimal_baseline__default_multihop__tick_size2" in summary_text
    assert ",2,default_multihop," in summary_text