"""Category browser: pick a topic (Numbers, Addition, ...) to see its levels."""
from __future__ import annotations

import customtkinter as ctk

from app.engine.categories import get_category_meta
from app.ui import theme


class CategoryMapFrame(ctk.CTkFrame):
    def __init__(self, app) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app

        self._build_header()

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self._build_categories()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(24, 16))

        ctk.CTkButton(
            header, text="🏠 Menu", font=theme.font_body(14), width=100, height=36,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._on_menu,
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="🗺️ Practice by Category", font=theme.font_title(26),
            text_color=theme.COLOR_PRIMARY,
        ).pack(side="left", padx=20)

    def _build_categories(self) -> None:
        engine = self.app.lesson_engine
        completed_ids = set(self.app.progress.get_completed_lesson_ids())

        for category in engine.categories():
            lessons = engine.lessons_in_category(category)
            meta = get_category_meta(category)
            completed_count = sum(1 for lesson in lessons if lesson.id in completed_ids)
            total = len(lessons)
            all_done = completed_count == total

            status = "✅ All levels complete!" if all_done else f"{completed_count}/{total} levels complete"

            ctk.CTkButton(
                self.body,
                text=f"{meta.icon}  {meta.title}\n{status}",
                font=theme.font_heading(18), anchor="w", height=76, corner_radius=16,
                fg_color=theme.COLOR_CARD, hover_color=theme.COLOR_PRIMARY_HOVER,
                text_color=theme.COLOR_TEXT,
                command=lambda c=category: self._on_open_category(c),
            ).pack(fill="x", pady=8)

    def _on_open_category(self, category: str) -> None:
        self.app.show_category_levels(category)

    def _on_menu(self) -> None:
        self.app.show_dashboard()
