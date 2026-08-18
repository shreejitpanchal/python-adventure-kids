"""Root application window: owns navigation between full-screen frames."""
from __future__ import annotations

import customtkinter as ctk

from app.config.settings import Settings, get_db_path, load_settings, save_settings
from app.engine.lesson_engine import LessonEngine
from app.engine.quiz_engine import QuizEngine
from app.progress.store import ProgressStore
from app.ui import theme
from app.ui.assets import apply_window_icon, ensure_windows_app_id
from app.ui.scroll_utils import install_fast_mousewheel_scrolling


class App(ctk.CTk):
    def __init__(self) -> None:
        ensure_windows_app_id()  # must happen before the first window is shown

        super().__init__()
        theme.apply_base_theme()

        self.settings: Settings = load_settings()
        theme.apply_theme(self.settings.theme)
        theme.apply_font(self.settings.font_family, self.settings.font_size)

        self.title("Python Adventure")
        self.geometry(f"{theme.WINDOW_WIDTH}x{theme.WINDOW_HEIGHT}")
        self.minsize(800, 600)
        self.configure(fg_color=theme.COLOR_BG)

        apply_window_icon(self)

        self.progress = ProgressStore(get_db_path())
        self.lesson_engine = LessonEngine()
        self.quiz_engine = QuizEngine()

        self._current_frame: ctk.CTkFrame | None = None
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._route_initial_screen()

    def _route_initial_screen(self) -> None:
        if not self.settings.setup_complete:
            self.show_setup_wizard()
        else:
            self.show_hub()

    def show_frame(self, frame: ctk.CTkFrame) -> None:
        if self._current_frame is not None:
            self._current_frame.destroy()
        self._current_frame = frame
        frame.pack(fill="both", expand=True)
        install_fast_mousewheel_scrolling(self)

    def show_setup_wizard(self) -> None:
        from app.ui.setup_wizard import SetupWizardFrame

        self.show_frame(SetupWizardFrame(self, on_complete=self.show_hub))

    def show_hub(self) -> None:
        from app.ui.learning_hub import HubFrame

        self.show_frame(HubFrame(self))

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

    def show_project_categories(self) -> None:
        from app.engine.categories import PROJECT_CATEGORIES
        from app.ui.category_map import CategoryMapFrame

        self.show_frame(CategoryMapFrame(self, category_filter=PROJECT_CATEGORIES, heading="🛠️ Build a Project"))

    def show_category_levels(self, category: str) -> None:
        from app.ui.category_levels import CategoryLevelsFrame

        self.show_frame(CategoryLevelsFrame(self, category))

    def show_quiz(self) -> None:
        from app.ui.quiz_screen import QuizScreen

        self.show_frame(QuizScreen(self))

    def show_course_map(self) -> None:
        from app.ui.course_map import CourseMapFrame

        self.show_frame(CourseMapFrame(self))

    def show_course_chapter(self, category: str) -> None:
        from app.ui.course_chapter import CourseChapterFrame

        self.show_frame(CourseChapterFrame(self, category))

    def show_course_quiz(self, lesson_id: str) -> None:
        from app.ui.course_quiz_screen import CourseQuizScreen

        self.show_frame(CourseQuizScreen(self, lesson_id))

    def show_lesson_or_quiz(self, lesson_id: str) -> None:
        lesson = self.lesson_engine.get(lesson_id)
        if lesson.is_quiz:
            self.show_course_quiz(lesson_id)
        else:
            self.show_lesson(lesson_id)

    def show_settings(self) -> None:
        from app.ui.settings_screen import SettingsFrame

        self.show_frame(SettingsFrame(self))

    def apply_and_persist_theme(self, theme_key: str) -> None:
        theme.apply_theme(theme_key)
        self.configure(fg_color=theme.COLOR_BG)
        self.settings.theme = theme_key
        self.save_settings()

    def apply_and_persist_font(self, family_key: str, size_key: str) -> None:
        theme.apply_font(family_key, size_key)
        self.settings.font_family = theme.CURRENT_FONT_FAMILY_KEY
        self.settings.font_size = theme.CURRENT_FONT_SIZE_KEY
        self.save_settings()

    def save_settings(self) -> None:
        save_settings(self.settings)

    def _on_close(self) -> None:
        self.progress.close()
        self.destroy()


def run_app() -> None:
    app = App()
    app.mainloop()
