import json
from pathlib import Path

import pytest

from sim.batch_comparison import compare_batch_dirs
from sim.comparison_artifact import build_comparison_artifact
from sim.comparison_catalog import (
    discover_comparison_artifacts,
    write_comparison_catalog,
)
from sim.experiment_artifacts import write_artifact_bundle
from sim.experiment_harness import ExperimentCase, ExperimentHarness


def create_fake_artifact(
    base_dir: Path,
    name: str,
    missing_file: str | None = None,
    bad_manifest: dict | None = None,
) -> Path:
    artifact_dir = base_dir / name
    artifact_dir.mkdir(parents=True, exist_ok=True)

    if missing_file != "comparison.csv":
        (artifact_dir / "comparison.csv").write_text(
            "case_name,status\n",
            encoding="utf-8",
        )

    if missing_file != "comparison.json":
        (artifact_dir / "comparison.json").write_text(
            "{}",
            encoding="utf-8",
        )

    if missing_file != "manifest.json":
        manifest = (
            bad_manifest
            if bad_manifest is not None
            else {
                "type": "comparison_artifact",
                "version": "1.0",
                "left_batch": {"path": "/fake/left_path"},
                "right_batch": {"path": "/fake/right_path"},
                "generated_at": "deterministic_run",
                "case_count": 12,
            }
        )
        (artifact_dir / "manifest.json").write_text(
            json.dumps(manifest, sort_keys=True),
            encoding="utf-8",
        )

    return artifact_dir


def test_deterministic_discovery_order(tmp_path):
    create_fake_artifact(tmp_path, "comparison_Z")
    create_fake_artifact(tmp_path, "comparison_A")
    create_fake_artifact(tmp_path, "comparison_M")

    artifacts = discover_comparison_artifacts(str(tmp_path))

    assert len(artifacts) == 3
    assert artifacts[0]["artifact_dir_name"] == "comparison_A"
    assert artifacts[1]["artifact_dir_name"] == "comparison_M"
    assert artifacts[2]["artifact_dir_name"] == "comparison_Z"


def test_valid_catalog_export(tmp_path):
    create_fake_artifact(tmp_path, "comparison_001")
    create_fake_artifact(tmp_path, "comparison_002")

    catalog_path = tmp_path / "comparison_catalog.json"
    written_path = write_comparison_catalog(str(tmp_path), str(catalog_path))

    data = json.loads(Path(written_path).read_text(encoding="utf-8"))

    assert data["type"] == "comparison_catalog"
    assert data["version"] == "1.0"
    assert data["artifact_count"] == 2
    assert len(data["artifacts"]) == 2
    assert data["artifacts"][0]["artifact_dir_name"] == "comparison_001"
    assert data["artifacts"][0]["case_count"] == 12
    assert data["artifacts"][0]["left_batch_path"] == "/fake/left_path"
    assert data["artifacts"][1]["artifact_dir_name"] == "comparison_002"


def test_invalid_artifact_missing_file_raises(tmp_path):
    create_fake_artifact(tmp_path, "comparison_bad", missing_file="comparison.json")

    with pytest.raises(ValueError) as excinfo:
        discover_comparison_artifacts(str(tmp_path))

    assert "missing required file 'comparison.json'" in str(excinfo.value)


def test_invalid_manifest_type_raises(tmp_path):
    bad_manifest = {
        "type": "wrong_type_identifier",
        "version": "1.0",
        "left_batch": {"path": "/fake/left"},
        "right_batch": {"path": "/fake/right"},
        "generated_at": "deterministic_run",
        "case_count": 12,
    }
    create_fake_artifact(tmp_path, "comparison_badtype", bad_manifest=bad_manifest)

    with pytest.raises(ValueError) as excinfo:
        discover_comparison_artifacts(str(tmp_path))

    assert "manifest type must be 'comparison_artifact'" in str(excinfo.value)


def test_invalid_manifest_version_raises(tmp_path):
    bad_manifest = {
        "type": "comparison_artifact",
        "version": "2.0",
        "left_batch": {"path": "/fake/left"},
        "right_batch": {"path": "/fake/right"},
        "generated_at": "deterministic_run",
        "case_count": 12,
    }
    create_fake_artifact(tmp_path, "comparison_badversion", bad_manifest=bad_manifest)

    with pytest.raises(ValueError) as excinfo:
        discover_comparison_artifacts(str(tmp_path))

    assert "manifest version must be '1.0'" in str(excinfo.value)


def test_invalid_manifest_missing_keys_raises(tmp_path):
    bad_manifest = {
        "type": "comparison_artifact",
        "version": "1.0",
    }
    create_fake_artifact(
        tmp_path,
        "comparison_missingkeys",
        bad_manifest=bad_manifest,
    )

    with pytest.raises(ValueError) as excinfo:
        discover_comparison_artifacts(str(tmp_path))

    assert "manifest missing required key 'left_batch'" in str(excinfo.value)


def test_invalid_manifest_nested_batch_shape_raises(tmp_path):
    bad_manifest = {
        "type": "comparison_artifact",
        "version": "1.0",
        "left_batch": "not_an_object",
        "right_batch": {"path": "/fake/right"},
        "generated_at": "deterministic_run",
        "case_count": 12,
    }
    create_fake_artifact(
        tmp_path,
        "comparison_bad_nested_shape",
        bad_manifest=bad_manifest,
    )

    with pytest.raises(ValueError) as excinfo:
        discover_comparison_artifacts(str(tmp_path))

    assert "manifest key 'left_batch' must be an object" in str(excinfo.value)


def test_invalid_manifest_case_count_type_raises(tmp_path):
    bad_manifest = {
        "type": "comparison_artifact",
        "version": "1.0",
        "left_batch": {"path": "/fake/left"},
        "right_batch": {"path": "/fake/right"},
        "generated_at": "deterministic_run",
        "case_count": "12",
    }
    create_fake_artifact(
        tmp_path,
        "comparison_bad_case_count",
        bad_manifest=bad_manifest,
    )

    with pytest.raises(ValueError) as excinfo:
        discover_comparison_artifacts(str(tmp_path))

    assert "manifest key 'case_count' must be an integer" in str(excinfo.value)


def test_repeated_export_is_byte_identical(tmp_path):
    create_fake_artifact(tmp_path, "comparison_stable_run")

    catalog_path_1 = tmp_path / "cat1.json"
    catalog_path_2 = tmp_path / "cat2.json"

    write_comparison_catalog(str(tmp_path), str(catalog_path_1))
    write_comparison_catalog(str(tmp_path), str(catalog_path_2))

    content_1 = catalog_path_1.read_text(encoding="utf-8")
    content_2 = catalog_path_2.read_text(encoding="utf-8")

    assert content_1 == content_2


def test_catalog_can_index_real_wave_59_artifacts(tmp_path):
    left_cases = [
        ExperimentCase(case_name="case-b", scenario_name="delayed_delivery"),
        ExperimentCase(case_name="case-a", scenario_name="default_multihop"),
    ]
    right_cases = [
        ExperimentCase(case_name="case-a", scenario_name="default_multihop"),
    ]

    left_results = ExperimentHarness.run_experiments(left_cases)
    right_results = ExperimentHarness.run_experiments(right_cases)

    left_dir = tmp_path / "left_batch"
    right_dir = tmp_path / "right_batch"

    write_artifact_bundle(left_results, str(left_dir), batch_label="left")
    write_artifact_bundle(right_results, str(right_dir), batch_label="right")

    comparison = compare_batch_dirs(str(left_dir), str(right_dir))

    comparisons_root = tmp_path / "comparisons"
    build_comparison_artifact(
        left_batch_path=str(left_dir),
        right_batch_path=str(right_dir),
        comparison_result=comparison,
        output_dir=str(comparisons_root),
        artifact_id="run_001",
        generated_at_label="stable_label",
    )

    catalog_path = comparisons_root / "comparison_catalog.json"
    written_path = write_comparison_catalog(
        str(comparisons_root),
        str(catalog_path),
    )

    catalog = json.loads(Path(written_path).read_text(encoding="utf-8"))

    assert catalog["type"] == "comparison_catalog"
    assert catalog["version"] == "1.0"
    assert catalog["artifact_count"] == 1
    assert len(catalog["artifacts"]) == 1

    entry = catalog["artifacts"][0]
    assert entry["artifact_dir_name"] == "comparison_run_001"
    assert entry["artifact_dir_path"] == str(
        (comparisons_root / "comparison_run_001").resolve()
    )
    assert entry["generated_at"] == "stable_label"
    assert entry["left_batch_path"] == str(left_dir.resolve())
    assert entry["right_batch_path"] == str(right_dir.resolve())
    assert entry["case_count"] == 2