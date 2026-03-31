#!/usr/bin/env bash
# How To Read a Book - Entry point wrapper
# Automatically handles venv activation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
VENV_BIN="$PROJECT_ROOT/.venv/bin"

# Check if venv exists
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "📦 Virtual environment not found. Running install.sh..."
    cd "$PROJECT_ROOT" && ./install.sh
fi

# Use venv python if available, otherwise fall back to system python
if [ -x "$VENV_BIN/python3" ]; then
    exec "$VENV_BIN/python3" "$SCRIPT_DIR/scripts/run.py" "$@"
else
    exec python3 "$SCRIPT_DIR/scripts/run.py" "$@"
fi
