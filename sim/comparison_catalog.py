import json
from pathlib import Path
from typing import Any, Dict, List


def _read_json_file(json_path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid comparison artifact '{json_path.parent}': "
            f"'{json_path.name}' is not valid JSON: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid comparison artifact '{json_path.parent}': "
            f"'{json_path.name}' must contain a JSON object"
        )
    return data


def _require_manifest_key(
    manifest_data: Dict[str, Any],
    artifact_dir: Path,
    key: str,
) -> Any:
    if key not in manifest_data:
        raise ValueError(
            f"Invalid comparison artifact '{artifact_dir}': "
            f"manifest missing required key '{key}'"
        )
    return manifest_data[key]


def _require_mapping_with_path(
    manifest_data: Dict[str, Any],
    artifact_dir: Path,
    key: str,
) -> str:
    value = _require_manifest_key(manifest_data, artifact_dir, key)
    if not isinstance(value, dict):
        raise ValueError(
            f"Invalid comparison artifact '{artifact_dir}': "
            f"manifest key '{key}' must be an object"
        )

    path_value = value.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise ValueError(
            f"Invalid comparison artifact '{artifact_dir}': "
            f"manifest key '{key}.path' must be a non-empty string"
        )
    return path_value


def _validate_manifest(artifact_dir: Path) -> Dict[str, Any]:
    manifest_path = artifact_dir / "manifest.json"
    manifest_data = _read_json_file(manifest_path)

    if manifest_data.get("type") != "comparison_artifact":
        raise ValueError(
            f"Invalid comparison artifact '{artifact_dir}': "
            "manifest type must be 'comparison_artifact'"
        )

    if manifest_data.get("version") != "1.0":
        raise ValueError(
            f"Invalid comparison artifact '{artifact_dir}': "
            "manifest version must be '1.0'"
        )

    left_batch_path = _require_mapping_with_path(
        manifest_data=manifest_data,
        artifact_dir=artifact_dir,
        key="left_batch",
    )
    right_batch_path = _require_mapping_with_path(
        manifest_data=manifest_data,
        artifact_dir=artifact_dir,
        key="right_batch",
    )

    generated_at = _require_manifest_key(
        manifest_data=manifest_data,
        artifact_dir=artifact_dir,
        key="generated_at",
    )
    if not isinstance(generated_at, str) or not generated_at:
        raise ValueError(
            f"Invalid comparison artifact '{artifact_dir}': "
            "manifest key 'generated_at' must be a non-empty string"
        )

    case_count = _require_manifest_key(
        manifest_data=manifest_data,
        artifact_dir=artifact_dir,
        key="case_count",
    )
    if not isinstance(case_count, int):
        raise ValueError(
            f"Invalid comparison artifact '{artifact_dir}': "
            "manifest key 'case_count' must be an integer"
        )

    manifest_data["_validated_left_batch_path"] = left_batch_path
    manifest_data["_validated_right_batch_path"] = right_batch_path
    return manifest_data


def discover_comparison_artifacts(root_dir: str) -> List[Dict[str, Any]]:
    """
    Wave-60: Discover and validate Wave-59 comparison artifacts under root_dir.
    Returns deterministically ordered catalog entries.
    """
    root_path = Path(root_dir).resolve()
    if not root_path.is_dir():
        raise ValueError(f"Root directory does not exist: {root_path}")

    candidates = sorted(
        (
            path
            for path in root_path.iterdir()
            if path.is_dir() and path.name.startswith("comparison_")
        ),
        key=lambda path: path.name,
    )

    artifacts: List[Dict[str, Any]] = []

    for candidate in candidates:
        required_files = [
            "comparison.csv",
            "comparison.json",
            "manifest.json",
        ]
        for file_name in required_files:
            file_path = candidate / file_name
            if not file_path.is_file():
                raise ValueError(
                    f"Invalid comparison artifact '{candidate}': "
                    f"missing required file '{file_name}'"
                )

        manifest_data = _validate_manifest(candidate)

        artifacts.append(
            {
                "artifact_dir_name": candidate.name,
                "artifact_dir_path": str(candidate),
                "case_count": manifest_data["case_count"],
                "generated_at": manifest_data["generated_at"],
                "left_batch_path": manifest_data["_validated_left_batch_path"],
                "right_batch_path": manifest_data["_validated_right_batch_path"],
            }
        )

    return artifacts


def write_comparison_catalog(root_dir: str, output_path: str) -> str:
    """
    Wave-60: Build and write comparison_catalog.json from the artifacts under root_dir.
    Returns the written absolute output path.
    """
    artifacts = discover_comparison_artifacts(root_dir)

    catalog_document = {
        "type": "comparison_catalog",
        "version": "1.0",
        "root_path": str(Path(root_dir).resolve()),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }

    output_file = Path(output_path).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(catalog_document, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return str(output_file)