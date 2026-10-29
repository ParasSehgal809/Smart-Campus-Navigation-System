#!/usr/bin/env bash
# Smart Campus Navigation System runner

# Locate python3 interpreter
if [ -x "/Users/parassehgal/.local/bin/python3.15" ]; then
    PYTHON_BIN="/Users/parassehgal/.local/bin/python3.15"
elif command -v python3 &> /dev/null; then
    PYTHON_BIN="$(command -v python3)"
else
    echo "Python 3 is required but was not found."
    exit 1
fi

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

case "$1" in
    web|server)
        ./run_web.sh
        ;;
    batch)
        ./run_batch.sh "${2:-all}"
        ;;
    demo)
        "$PYTHON_BIN" demo.py
        ;;
    test)
        "$PYTHON_BIN" test_campus.py
        ;;
    map)
        "$PYTHON_BIN" -c "from campus_graph import build_default_campus; from visualizer import generate_interactive_html; generate_interactive_html(build_default_campus()); print('Interactive map generated at: campus_map.html')"
        if command -v open &> /dev/null; then
            open campus_map.html
        fi
        ;;
    *)
        "$PYTHON_BIN" main.py
        ;;
esac
