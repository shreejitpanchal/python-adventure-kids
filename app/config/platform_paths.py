"""Resolves the real, writable directory this app's data lives in.

Windows and Android need genuinely different answers, since there's no
shared notion of "a folder next to the app" once this is a packaged,
sandboxed install rather than a repo checkout.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_FOLDER_NAME = "PythonAdventure"


def resolve_platform_data_dir() -> Path:
    """Returns the OS-appropriate writable data directory, creating it if
    it doesn't exist yet. Pure path resolution -- doesn't read or write any
    app data files itself, and doesn't know about migrating old data
    forward (see app.config.settings.get_data_dir for that)."""
    android_dir = os.environ.get("FLET_APP_STORAGE_DATA")
    if android_dir:
        # Set by the Flet runtime on Android (and other packaged builds) --
        # a real per-app writable directory, already the process's working
        # directory. Resolved to an absolute Path explicitly here so this
        # function's contract is the same on every platform.
        data_dir = Path(android_dir)
    elif sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        data_dir = (Path(appdata) if appdata else Path.home()) / APP_FOLDER_NAME
    else:
        # macOS/Linux dev runs -- not a real target platform for this app
        # yet, but shouldn't crash outright.
        data_dir = Path.home() / f".{APP_FOLDER_NAME.lower()}"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
