#!/usr/bin/env python3
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from aether_phase6_presentation.builder import PresentationBuilder  # noqa: E402
from aether_phase6_runtime.benchmarks import (  # noqa: E402
    RuntimeBenchmarkRunner,
    default_runtime_benchmark_scenarios,
)
from aether_phase6_runtime.report import BenchmarkReportBuilder  # noqa: E402


def main() -> None:
    runner = RuntimeBenchmarkRunner()
    scenarios = default_runtime_benchmark_scenarios()
    suite = runner.run_suite("presentation_export", scenarios)

    report = BenchmarkReportBuilder().build(suite)
    presentation = PresentationBuilder().build(report.structured)

    print(json.dumps(presentation.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()