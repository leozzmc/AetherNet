import csv
import io
import pytest
from pathlib import Path

from sim.batch_comparison import (
    read_batch_summary,
    compare_batch_dirs,
    compare_batches_from_catalog,
    comparison_to_json,
)
from sim.experiment_harness import ExperimentCase, ExperimentHarness
from sim.experiment_artifacts import write_artifact_bundle


def create_dummy_summary_csv(bundle_dir: Path, rows_data: list):
    bundle_dir.mkdir(parents=True, exist_ok=True)
    csv_path = bundle_dir / "summary.csv"

    if not rows_data:
        csv_path.write_text("case_name,delivery_ratio\n", encoding="utf-8")
        return bundle_dir

    keys = rows_data[0].keys()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=keys, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows_data)

    csv_path.write_text(output.getvalue(), encoding="utf-8")
    return bundle_dir


def test_summary_reader_parses_csv_correctly(tmp_path):
    bundle_dir = tmp_path / "batch_A"
    create_dummy_summary_csv(
        bundle_dir,
        [
            {"case_name": "case-1", "delivery_ratio": "0.5"},
            {"case_name": "case-2", "delivery_ratio": "0.8"},
        ],
    )

    rows = read_batch_summary(str(bundle_dir))

    assert len(rows) == 2
    assert rows[0]["case_name"] == "case-1"
    assert rows[0]["delivery_ratio"] == 0.5
    assert rows[1]["case_name"] == "case-2"
    assert rows[1]["delivery_ratio"] == 0.8


def test_comparison_preserves_deterministic_case_ordering(tmp_path):
    dir_left = create_dummy_summary_csv(
        tmp_path / "left",
        [
            {"case_name": "Z-case", "delivery_ratio": "0.1"},
            {"case_name": "A-case", "delivery_ratio": "0.2"},
        ],
    )
    dir_right = create_dummy_summary_csv(
        tmp_path / "right",
        [
            {"case_name": "Z-case", "delivery_ratio": "0.1"},
            {"case_name": "A-case", "delivery_ratio": "0.2"},
        ],
    )

    comp = compare_batch_dirs(str(dir_left), str(dir_right))

    assert comp["total_cases_compared"] == 2
    assert comp["rows"][0]["case_name"] == "A-case"
    assert comp["rows"][1]["case_name"] == "Z-case"


def test_explicit_missing_side_rows(tmp_path):
    dir_left = create_dummy_summary_csv(
        tmp_path / "left",
        [
            {"case_name": "shared", "delivery_ratio": "0.5"},
            {"case_name": "only-left", "delivery_ratio": "0.4"},
        ],
    )
    dir_right = create_dummy_summary_csv(
        tmp_path / "right",
        [
            {"case_name": "shared", "delivery_ratio": "0.6"},
            {"case_name": "only-right", "delivery_ratio": "0.8"},
        ],
    )

    comp = compare_batch_dirs(str(dir_left), str(dir_right))

    assert comp["total_cases_compared"] == 3

    r_left = next(r for r in comp["rows"] if r["case_name"] == "only-left")
    assert r_left["left_present"] is True
    assert r_left["right_present"] is False
    assert r_left["right_delivery_ratio"] is None
    assert r_left["delivery_ratio_delta"] is None

    r_right = next(r for r in comp["rows"] if r["case_name"] == "only-right")
    assert r_right["left_present"] is False
    assert r_right["right_present"] is True
    assert r_right["left_delivery_ratio"] is None
    assert r_right["delivery_ratio_delta"] is None


def test_correct_delta_calculation(tmp_path):
    dir_left = create_dummy_summary_csv(
        tmp_path / "left",
        [
            {"case_name": "improving", "delivery_ratio": "0.2"},
            {"case_name": "degrading", "delivery_ratio": "0.9"},
        ],
    )
    dir_right = create_dummy_summary_csv(
        tmp_path / "right",
        [
            {"case_name": "improving", "delivery_ratio": "0.5"},
            {"case_name": "degrading", "delivery_ratio": "0.8"},
        ],
    )

    comp = compare_batch_dirs(str(dir_left), str(dir_right))

    r_imp = next(r for r in comp["rows"] if r["case_name"] == "improving")
    assert round(r_imp["delivery_ratio_delta"], 4) == 0.3

    r_deg = next(r for r in comp["rows"] if r["case_name"] == "degrading")
    assert round(r_deg["delivery_ratio_delta"], 4) == -0.1


def test_catalog_aware_comparison_works(tmp_path):
    dir_left = create_dummy_summary_csv(tmp_path / "left", [])
    dir_right = create_dummy_summary_csv(tmp_path / "right", [])

    catalog = {
        "batches": [
            {"batch_label": "baseline", "path": str(dir_left)},
            {"batch_label": "experiment", "path": str(dir_right)},
        ]
    }

    comp = compare_batches_from_catalog(catalog, "baseline", "experiment")
    assert comp["total_cases_compared"] == 0
    assert "left" in comp["left_batch_dir"]
    assert "right" in comp["right_batch_dir"]


def test_catalog_aware_raises_on_missing_label():
    catalog = {"batches": []}

    with pytest.raises(ValueError) as excinfo:
        compare_batches_from_catalog(catalog, "missing1", "missing2")

    assert "not found in catalog" in str(excinfo.value)


def test_deterministic_json_output(tmp_path):
    dir_left = create_dummy_summary_csv(
        tmp_path / "left",
        [{"case_name": "A", "delivery_ratio": "0.1"}],
    )
    dir_right = create_dummy_summary_csv(
        tmp_path / "right",
        [{"case_name": "A", "delivery_ratio": "0.2"}],
    )

    comp = compare_batch_dirs(str(dir_left), str(dir_right))

    json_1 = comparison_to_json(comp)
    json_2 = comparison_to_json(comp)

    assert json_1 == json_2
    assert '"delivery_ratio_delta": 0.1' in json_1


def test_works_with_real_artifacts(tmp_path):
    cases = [
        ExperimentCase(
            case_name="real-case",
            scenario_name="default_multihop",
            tick_size=1,
            simulation_end_override=5,
        )
    ]
    results = ExperimentHarness.run_experiments(cases)

    dir_left = tmp_path / "real_left"
    dir_right = tmp_path / "real_right"
    write_artifact_bundle(results, str(dir_left), batch_label="real_left")
    write_artifact_bundle(results, str(dir_right), batch_label="real_right")

    comp = compare_batch_dirs(str(dir_left), str(dir_right))

    assert comp["total_cases_compared"] == 1
    assert comp["rows"][0]["case_name"] == "real-case"
    assert comp["rows"][0]["left_present"] is True
    assert comp["rows"][0]["right_present"] is True
    assert comp["rows"][0]["delivery_ratio_delta"] == 0.0