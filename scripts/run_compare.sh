#!/bin/sh
set -e

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
export PYTHONPATH="$REPO_ROOT"

echo "=== AetherNet Scenario Comparison Runner ==="

# All complex execution logic has been properly abstracted into the run_helpers module.
python3 "$REPO_ROOT/sim/run_helpers.py"

echo "=== Comparison Complete ==="