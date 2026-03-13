import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List

from sim.scenarios import get_scenario, list_scenarios
from sim.simulator import create_default_simulator
from sim.reporting import write_json_report, compare_reports

def run_named_scenario(
    scenario_name: str, 
    tick_size: int = 1, 
    end_time_override: int = None,
    output_path: str | Path = None
) -> Dict[str, Any]:
    """
    Executes a single scenario by name, handling all temporary plan files and storage logic.
    Optionally writes the report to disk.
    """
    profile = get_scenario(scenario_name)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding="utf-8") as plan_file:
        json.dump(profile.generate_plan(), plan_file)
        plan_path = plan_file.name
        
    try:
        with tempfile.TemporaryDirectory() as tmpstore:
            simulator, _ = create_default_simulator(
                plan_path=plan_path,
                store_dir=tmpstore,
                scenario_name=profile.name,
                inject_short_lived=profile.inject_short_lived_bundle,
                tick_size=tick_size,
                simulation_end_override=end_time_override
            )
            report = simulator.run()
            
            if output_path:
                write_json_report(report, output_path)
                
            return report
    finally:
        Path(plan_path).unlink(missing_ok=True)

def run_all_scenarios(reports_dir: str | Path, comparison_out_path: str | Path) -> Dict[str, Any]:
    """
    Executes all registered built-in scenarios sequentially.
    Saves individual reports and an aggregate comparison to the specified directories.
    """
    reports_dir = Path(reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    all_reports = []
    scenarios = list_scenarios()
    
    print(f"Running {len(scenarios)} built-in scenarios...")
    
    for name in scenarios:
        print(f"\n--- Running: {name} ---")
        report_path = reports_dir / f"{name}.json"
        report = run_named_scenario(name, output_path=report_path)
        all_reports.append(report)
        print(f"Saved report: {report_path}")
        
    print("\n--- Generating Aggregate Comparison ---")
    comparison = compare_reports(all_reports)
    write_json_report(comparison, comparison_out_path)
    print(f"Saved aggregate comparison: {comparison_out_path}")
    
    return comparison

if __name__ == "__main__":
    # Provides a clean entrypoint for the run_compare.sh script
    import sys
    repo_root = Path(__file__).resolve().parents[1]
    artifacts_dir = repo_root / "artifacts"
    
    run_all_scenarios(
        reports_dir=artifacts_dir / "reports",
        comparison_out_path=artifacts_dir / "comparison.json"
    )