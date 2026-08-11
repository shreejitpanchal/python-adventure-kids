"""Root application window: owns navigation between full-screen frames."""
from __future__ import annotations

import customtkinter as ctk

from app.config.settings import Settings, get_db_path, load_settings, save_settings
from app.engine.lesson_engine import LessonEngine
from app.progress.store import ProgressStore
from app.ui import theme


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        theme.apply_base_theme()

        self.title("Python Adventure")
        self.geometry(f"{theme.WINDOW_WIDTH}x{theme.WINDOW_HEIGHT}")
        self.minsize(800, 600)
        self.configure(fg_color=theme.COLOR_BG)

        self.settings: Settings = load_settings()
        self.progress = ProgressStore(get_db_path())
        self.lesson_engine = LessonEngine()

        self._current_frame: ctk.CTkFrame | None = None
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._route_initial_screen()

    def _route_initial_screen(self) -> None:
        if not self.settings.setup_complete:
            self.show_setup_wizard()
        else:
            self.show_dashboard()

    def show_frame(self, frame: ctk.CTkFrame) -> None:
        if self._current_frame is not None:
            self._current_frame.destroy()
        self._current_frame = frame
        frame.pack(fill="both", expand=True)

    def show_setup_wizard(self) -> None:
        from app.ui.setup_wizard import SetupWizardFrame

        self.show_frame(SetupWizardFrame(self, on_complete=self.show_dashboard))

    def show_dashboard(self) -> None:
        from app.ui.dashboard import DashboardFrame

        self.progress.record_play_today()
        self.show_frame(DashboardFrame(self))

    def show_lesson(self, lesson_id: str) -> None:
        from app.ui.lesson_screen import LessonScreen

        self.show_frame(LessonScreen(self, lesson_id))

    def show_category_map(self) -> None:
        from app.ui.category_map import CategoryMapFrame

        self.show_frame(CategoryMapFrame(self))

    def show_category_levels(self, category: str) -> None:
        from app.ui.category_levels import CategoryLevelsFrame

        self.show_frame(CategoryLevelsFrame(self, category))

    def save_settings(self) -> None:
        save_settings(self.settings)

    def _on_close(self) -> None:
        self.progress.close()
        self.destroy()


def run_app() -> None:
    app = App()
    app.mainloop()
