"""Shared app state for the Flet UI: settings, progress store, lesson
engine, and the current theme -- built once in app_window_flet.main() and
threaded through every view-builder function as an explicit parameter
(no global state, no framework-managed dependency injection)."""
from __future__ import annotations

from app.config.settings import Settings, get_db_path, load_settings, save_settings
from app.engine.lesson_engine import LessonEngine
from app.engine.quiz_engine import QuizEngine
from app.progress.store import ProgressStore
from app.ui.theme_flet import ThemePreset, get_preset


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

    @property
    def theme(self) -> ThemePreset:
        return get_preset(self.settings.theme)

    def apply_theme(self, theme_key: str) -> None:
        self.settings.theme = theme_key
        self.save_settings()

    def save_settings(self) -> None:
        save_settings(self.settings)

    def close(self) -> None:
        self.progress.close()
