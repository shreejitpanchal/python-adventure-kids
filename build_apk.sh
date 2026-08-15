#!/usr/bin/env bash
# Builds an Android APK of the Flet re-platform (main_flet.py) from the
# current source tree -- NOT the CustomTkinter app (main.py), which has no
# Android build at all. `flet build` drives a real Flutter SDK + Android
# SDK/NDK under the hood; see https://flet.dev/docs/publish/android for
# first-time toolchain setup. This script assumes that's already installed
# and just runs the build.
set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

venv_bin() {
    # $1: posix-style script name without extension, e.g. "python" or "flet"
    if [ -f ".venv/Scripts/$1.exe" ]; then
        echo ".venv/Scripts/$1.exe"
    elif [ -f ".venv/bin/$1" ]; then
        echo ".venv/bin/$1"
    else
        echo ""
    fi
}

PYEXE="$(venv_bin python)"
FLETEXE="$(venv_bin flet)"

if [ -z "$PYEXE" ] || [ -z "$FLETEXE" ]; then
    echo "No .venv found (or it's missing the flet package) -- run run.bat/run.sh once first to set it up."
    exit 1
fi

# `flutter` isn't a pip dependency -- flet build shells out to a real
# Flutter SDK install, which isn't guaranteed to be on PATH. Look there
# first, then fall back to $FLUTTER_HOME, then this machine's known
# install location as a last resort.
if ! command -v flutter >/dev/null 2>&1; then
    if [ -n "$FLUTTER_HOME" ] && [ -x "$FLUTTER_HOME/bin/flutter" ]; then
        export PATH="$FLUTTER_HOME/bin:$PATH"
    elif [ -x "$HOME/flutter/3.44.8/bin/flutter" ]; then
        export PATH="$HOME/flutter/3.44.8/bin:$PATH"
    else
        echo "Flutter SDK not found on PATH."
        echo "Install it (https://docs.flutter.dev/get-started/install), then either"
        echo "put its bin/ on PATH or set FLUTTER_HOME to the SDK root and re-run."
        exit 1
    fi
fi

echo "Building Android APK from main_flet.py..."
echo

# flet build's own CLI output (via `rich`) includes emoji (checkmarks etc.);
# on Windows, a subprocess's stdout can default to the legacy cp1252 console
# codepage instead of UTF-8, which crashes on those characters before the
# build even starts. Force UTF-8 regardless of the console's codepage.
export PYTHONUTF8=1

# --module-name is required: flet build defaults to main.py, which is the
# unrelated CustomTkinter app in this repo, not the Flet one.
"$FLETEXE" build apk --module-name main_flet --yes "$@"

echo
echo "Done -- APK at build/apk/python-adventure.apk"
