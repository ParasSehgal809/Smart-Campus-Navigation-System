#!/usr/bin/env bash
# run_batch.sh - Runs the Campus Batch Navigation & Traffic Congestion Engine

if [ -x "/Users/parassehgal/.local/bin/python3.15" ]; then
    PYTHON_BIN="/Users/parassehgal/.local/bin/python3.15"
elif command -v python3 &> /dev/null; then
    PYTHON_BIN="$(command -v python3)"
else
    echo "Error: Python 3 not found."
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

SCENARIO="${1:-all}"
echo "Running Batch Navigation Simulation for scenario: $SCENARIO..."
"$PYTHON_BIN" batch_navigator.py --scenario "$SCENARIO" --csv batch_results.csv
