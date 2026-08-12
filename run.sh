#!/usr/bin/env bash
# Launches Python Adventure -- sets up the virtual environment on first run.
set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

venv_python() {
    if [ -f ".venv/Scripts/python.exe" ]; then
        echo ".venv/Scripts/python.exe"
    elif [ -f ".venv/bin/python" ]; then
        echo ".venv/bin/python"
    else
        echo ""
    fi
}

PYEXE="$(venv_python)"

if [ -z "$PYEXE" ]; then
    echo "============================================"
    echo "  Setting up Python Adventure for the"
    echo "  first time. This only happens once and"
    echo "  may take a minute..."
    echo "============================================"
    echo

    if command -v python >/dev/null 2>&1; then
        PY=python
    elif command -v python3 >/dev/null 2>&1; then
        PY=python3
    else
        echo "Python was not found on this computer."
        echo "Please install Python from https://python.org then run this again."
        read -p "Press Enter to close..."
        exit 1
    fi

    "$PY" -m venv .venv
    PYEXE="$(venv_python)"

    "$PYEXE" -m pip install --upgrade pip
    "$PYEXE" -m pip install -r requirements.txt

    echo
    echo "Setup complete!"
    echo
fi

"$PYEXE" main.py
