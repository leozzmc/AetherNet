import json
from pathlib import Path
from typing import Any, Dict


def read_artifact_bundle(bundle_dir: str) -> Dict[str, Any]:
    """
    Wave-56: Reads and strictly validates a single artifact bundle.
    Raises ValueError if any required file is missing.
    """
    bundle_path = Path(bundle_dir).resolve()
    
    if not bundle_path.is_dir():
        raise ValueError(f"Artifact bundle directory does not exist: {bundle_path}")

    required_files = ["summary.csv", "summary.json", "manifest.json"]
    for file_name in required_files:
        if not (bundle_path / file_name).is_file():
            raise ValueError(f"Invalid bundle '{bundle_path.name}': Missing required file '{file_name}'.")

    manifest_path = bundle_path / "manifest.json"
    
    try:
        manifest_content = manifest_path.read_text(encoding="utf-8")
        manifest_dict = json.loads(manifest_content)
    except Exception as e:
        raise ValueError(f"Failed to parse manifest.json in bundle '{bundle_path.name}': {e}")

    # Inject the absolute path so the catalog knows where this bundle lives
    manifest_dict["path"] = str(bundle_path)
    return manifest_dict


def build_artifact_catalog(root_dir: str) -> Dict[str, Any]:
    """
    Wave-56: Scans a root directory for immediate child bundle directories,
    sorts them deterministically, and builds a consolidated catalog.
    """
    root_path = Path(root_dir).resolve()
    
    if not root_path.is_dir():
        raise ValueError(f"Catalog root directory does not exist: {root_path}")

    # Scan immediate children only, filter for directories
    child_dirs = [p for p in root_path.iterdir() if p.is_dir()]
    
    # Deterministic sorting by directory name
    child_dirs.sort(key=lambda p: p.name)

    batches = []
    for bundle_path in child_dirs:
        # Strict validation: let it raise if the directory is not a valid bundle
        manifest = read_artifact_bundle(str(bundle_path))
        
        # Extract a curated subset of manifest fields for the catalog summary
        batch_entry = {
            "batch_label": manifest.get("batch_label", "unknown"),
            "artifact_version": manifest.get("artifact_version", "unknown"),
            "total_cases": manifest.get("total_cases", 0),
            "case_names": manifest.get("case_names", []),
            "path": manifest.get("path", str(bundle_path)),
            "directory_name": bundle_path.name
        }
        batches.append(batch_entry)

    return {
        "total_batches": len(batches),
        "batches": batches
    }


def catalog_to_json(catalog: Dict[str, Any]) -> str:
    """
    Serializes the catalog dictionary to a deterministic JSON string.
    """
    return json.dumps(catalog, indent=2, sort_keys=True)


def write_artifact_catalog(root_dir: str, output_path: str) -> str:
    """
    Builds the catalog from root_dir and writes it to output_path.
    Returns the absolute path to the written catalog JSON file.
    """
    catalog = build_artifact_catalog(root_dir)
    json_content = catalog_to_json(catalog)
    
    out_file = Path(output_path).resolve()
    if out_file.parent:
        out_file.parent.mkdir(parents=True, exist_ok=True)
        
    out_file.write_text(json_content, encoding="utf-8")
    return str(out_file)