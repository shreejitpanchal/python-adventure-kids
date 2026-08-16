"""App version info shown in Settings: pyproject.toml's [project] version
plus a build number incremented by build_apk.sh on every Android build
(BUILD_NUMBER at the repo root -- see that script for why). Both are read
from plain files at runtime rather than hardcoded, so a compiled APK
(which bundles the whole source tree, BUILD_NUMBER included) always shows
the exact version/build it was actually built from -- useful once a
parent has tested a few different builds on a device and wants to
confirm which one is currently installed.
"""
from __future__ import annotations

import tomllib

from app.config.settings import get_repo_root


def get_app_version() -> str:
    """e.g. "1.0.0", from pyproject.toml's [project] version. "unknown" if
    that file is missing or malformed -- should never happen in a real
    checkout, but this is display-only info, not worth crashing over."""
    try:
        data = tomllib.loads((get_repo_root() / "pyproject.toml").read_text(encoding="utf-8"))
        return str(data["project"]["version"])
    except (OSError, KeyError, tomllib.TOMLDecodeError):
        return "unknown"


def get_build_number() -> str:
    """The integer in BUILD_NUMBER at the repo root, or "dev" if that
    file doesn't exist yet (e.g. a fresh checkout before the first
    build_apk.sh run) -- never crashes, just falls back to a label that
    makes it obvious this isn't a tagged build."""
    try:
        return get_repo_root().joinpath("BUILD_NUMBER").read_text(encoding="utf-8").strip()
    except OSError:
        return "dev"


def get_version_label() -> str:
    """e.g. "v1.0.0 (build 3)" -- what Settings actually displays."""
    return f"v{get_app_version()} (build {get_build_number()})"
