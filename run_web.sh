#!/usr/bin/env bash
# run_web.sh - Starts the Smart Campus Navigation Web Server and opens browser

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

PORT=8000

# Open browser in background after 1 second
(
    sleep 1
    if command -v open &> /dev/null; then
        open "http://localhost:${PORT}"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "http://localhost:${PORT}"
    fi
) &

echo "Starting Campus Navigation Web Server on http://localhost:${PORT}..."
"$PYTHON_BIN" server.py "$PORT"
