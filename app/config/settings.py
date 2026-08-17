"""Application configuration: data directory, persisted settings, first-run state."""
from __future__ import annotations

import hashlib
import json
import secrets
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.config.platform_paths import resolve_platform_data_dir

APP_FOLDER_NAME = "PythonAdventure"
SETTINGS_FILENAME = "settings.json"
DB_FILENAME = "progress.sqlite3"

# The dev-convenience location used before this app moved to a proper
# per-user OS directory (see app.config.platform_paths). Kept only so
# get_data_dir() can migrate anything left there forward one time.
REPO_LOCAL_DATA_DIRNAME = "app-data"


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def get_data_dir() -> Path:
    """Return the app data directory, creating it if needed.

    The actual OS-appropriate location comes from
    app.config.platform_paths.resolve_platform_data_dir() -- a proper
    per-user directory on Windows, Flet's app-sandboxed storage directory
    on Android. Anything left over in this repo's old app-data/
    dev-convenience location is copied forward automatically, so moving
    where data lives never resets a child's progress.
    """
    data_dir = resolve_platform_data_dir()
    _migrate_from_repo_local_dir(data_dir)
    return data_dir


def _migrate_from_repo_local_dir(data_dir: Path) -> None:
    """One-time copy from the repo-local app-data/ folder. Never overwrites
    a file that already exists at the destination."""
    old_dir = get_repo_root() / REPO_LOCAL_DATA_DIRNAME
    if old_dir == data_dir or not old_dir.is_dir():
        return
    for filename in (SETTINGS_FILENAME, DB_FILENAME):
        old_file = old_dir / filename
        new_file = data_dir / filename
        if old_file.is_file() and not new_file.exists():
            shutil.copy2(old_file, new_file)


def get_db_path() -> Path:
    return get_data_dir() / DB_FILENAME


def get_settings_path() -> Path:
    return get_data_dir() / SETTINGS_FILENAME


@dataclass
class Settings:
    child_name: str = ""
    sound_enabled: bool = True
    animations_enabled: bool = True
    reduced_motion: bool = False
    theme: str = "midnight_dark"
    font_family: str = "default"
    """A semantic key (not a real font name) -- each UI maps this to its own
    concrete, platform-appropriate font via a FONT_FAMILY_PRESETS-style dict
    (see app/ui/theme.py for CTk, app/ui/theme_flet.py for Flet), the same
    pattern `theme` above uses for colors. An unrecognized key (e.g. a CTk-
    only key read back by the Flet app) falls back to that UI's default."""
    font_size: str = "medium"
    """One of small/medium/large/extra_large -- each UI maps this to its own
    size-scaling multiplier, same fallback-safe pattern as font_family."""
    parent_pin_salt: str = ""
    parent_pin_hash: str = ""
    setup_complete: bool = False

    def has_parent_pin(self) -> bool:
        return bool(self.parent_pin_hash)

    def set_parent_pin(self, pin: str) -> None:
        salt = secrets.token_hex(16)
        self.parent_pin_salt = salt
        self.parent_pin_hash = _hash_pin(pin, salt)

    def verify_parent_pin(self, pin: str) -> bool:
        if not self.has_parent_pin():
            return False
        return _hash_pin(pin, self.parent_pin_salt) == self.parent_pin_hash


def _hash_pin(pin: str, salt: str) -> str:
    return hashlib.sha256((salt + pin).encode("utf-8")).hexdigest()


def load_settings() -> Settings:
    path = get_settings_path()
    if not path.exists():
        return Settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Settings()
    known_fields = {f for f in Settings.__dataclass_fields__}
    filtered = {k: v for k, v in data.items() if k in known_fields}
    return Settings(**filtered)


def save_settings(settings: Settings) -> None:
    path = get_settings_path()
    path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")


def is_first_run() -> bool:
    return not load_settings().setup_complete
