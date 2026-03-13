#!/bin/sh
set -e

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)

echo "=== Resetting AetherNet Environment ==="
echo "Cleaning up generated payloads..."
rm -rf "$REPO_ROOT/payloads/telemetry/"*
rm -rf "$REPO_ROOT/payloads/science/"*

echo "Environment reset complete. Ready for a clean run."