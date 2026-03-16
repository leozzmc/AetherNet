from pathlib import Path
from typing import Any, Dict, Union

from sim.reporting import write_json_report
from sim.research_visualization import build_visualization_spec_from_experiment_batch


def export_experiment_artifacts(batch_result: Dict[str, Any], output_dir: Union[str, Path]) -> Dict[str, str]:
    """
    Wave-36: Deterministic artifact export layer for experiment results.
    
    Exports the outputs of an experiment batch (and its derived visualization spec) 
    into a stable, on-disk JSON artifact structure. This makes the results immediately 
    usable by notebooks, external analysis tools, or portfolio demonstrations.
    """
    if not isinstance(batch_result, dict):
        raise ValueError("batch_result must be a dictionary.")

    required_keys = ["experiment_names", "results", "aggregate_comparison"]
    for key in required_keys:
        if key not in batch_result:
            raise ValueError(f"batch_result is missing required key: '{key}'")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build the visualization spec cleanly from the batch result
    vis_spec = build_visualization_spec_from_experiment_batch(batch_result)

    # Define deterministic file paths
    batch_result_path = out_dir / "batch_result.json"
    aggregate_comparison_path = out_dir / "aggregate_comparison.json"
    visualization_spec_path = out_dir / "visualization_spec.json"
    manifest_path = out_dir / "manifest.json"

    # Build the descriptive manifest
    manifest = {
        "source": "AetherNet Wave-36 artifact export",
        "experiment_count": len(batch_result["experiment_names"]),
        "experiment_names": batch_result["experiment_names"],
        "exported_files": {
            "batch_result": batch_result_path.name,
            "aggregate_comparison": aggregate_comparison_path.name,
            "visualization_spec": visualization_spec_path.name,
            "manifest": manifest_path.name,
        }
    }

    # Write files deterministically using the existing helper
    write_json_report(batch_result, batch_result_path)
    write_json_report(batch_result["aggregate_comparison"], aggregate_comparison_path)
    write_json_report(vis_spec, visualization_spec_path)
    write_json_report(manifest, manifest_path)

    # Return a mapping of logical artifact names to their absolute paths
    return {
        "batch_result": str(batch_result_path),
        "aggregate_comparison": str(aggregate_comparison_path),
        "visualization_spec": str(visualization_spec_path),
        "manifest": str(manifest_path),
    }