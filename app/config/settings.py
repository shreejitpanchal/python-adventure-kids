"""Application configuration: data directory, persisted settings, first-run state."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
from dataclasses import asdict, dataclass, field
from pathlib import Path

APP_FOLDER_NAME = "PythonAdventure"
SETTINGS_FILENAME = "settings.json"


def get_data_dir() -> Path:
    """Return the per-user app data directory, creating it if needed."""
    base = os.environ.get("APPDATA") or str(Path.home())
    data_dir = Path(base) / APP_FOLDER_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    return get_data_dir() / "progress.sqlite3"


def get_settings_path() -> Path:
    return get_data_dir() / SETTINGS_FILENAME


@dataclass
class Settings:
    child_name: str = ""
    sound_enabled: bool = True
    animations_enabled: bool = True
    reduced_motion: bool = False
    theme: str = "light"
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
