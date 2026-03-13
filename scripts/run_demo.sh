#!/bin/sh
set -e

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
export PYTHONPATH="$REPO_ROOT"

# Pass all script arguments directly to the python simulator
python3 "$REPO_ROOT/sim/simulator.py" "$@"