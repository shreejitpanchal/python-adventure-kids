"""Shared app state for the Flet UI: settings, progress store, lesson
engine, and the current theme -- built once in app_window_flet.main() and
threaded through every view-builder function as an explicit parameter
(no global state, no framework-managed dependency injection)."""
from __future__ import annotations

from app.config.settings import Settings, get_db_path, load_settings, save_settings
from app.engine.lesson_engine import LessonEngine
from app.engine.quiz_engine import QuizEngine
from app.progress.store import ProgressStore
from app.ui.theme_flet import (
    ThemePreset, get_preset, resolve_font_family, resolve_font_scale,
)


class AppState:
    def __init__(self) -> None:
        self.settings: Settings = load_settings()
        self.progress = ProgressStore(get_db_path())
        self.lesson_engine = LessonEngine()
        self.quiz_engine = QuizEngine()
        # Set once by app_window_flet.main() after a real ft.Page exists --
        # stays None here and in every test that constructs AppState
        # directly, so sound-playing call sites must guard for that (see
        # app/ui/lesson_screen_flet.py's _play_success_sounds()).
        self.sound_player = None
        # Stays None for the same reason sound_player does: ft.FilePicker
        # renders as an "Unknown control: FilePicker" red banner on the
        # generic Flet live-preview client (confirmed via real-device
        # Android testing) -- and since it self-registers into
        # page.overlay, which is attached at startup regardless of route,
        # it broke app launch entirely, not just the Settings screen it's
        # actually used from. Settings' Export/Import handlers guard for
        # this being None and show a friendly message instead of crashing
        # (see settings_screen_flet.py's _build_progress_card()). Tests
        # that need one inject a fake with matching async
        # save_file()/pick_files() methods.
        self.file_picker = None

    @property
    def theme(self) -> ThemePreset:
        return get_preset(self.settings.theme)

    @property
    def font_family(self) -> str:
        return resolve_font_family(self.settings.font_family)

    @property
    def font_scale(self) -> float:
        return resolve_font_scale(self.settings.font_size)

    def apply_theme(self, theme_key: str) -> None:
        self.settings.theme = theme_key
        self.save_settings()

    def apply_font(self, family_key: str, size_key: str) -> None:
        self.settings.font_family = family_key
        self.settings.font_size = size_key
        self.save_settings()

    def save_settings(self) -> None:
        save_settings(self.settings)

    def close(self) -> None:
        self.progress.close()
