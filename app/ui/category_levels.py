"""Levels within one category: play the next unlocked level, replay a completed
one, or see upcoming levels locked until the one before them is finished."""
from __future__ import annotations

import customtkinter as ctk

from app.engine.categories import get_category_meta
from app.ui import theme
from app.ui.color_utils import contrasting_text_color


class CategoryLevelsFrame(ctk.CTkFrame):
    def __init__(self, app, category: str) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app
        self.category = category

        self._build_header()

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self._build_levels()

    def _build_header(self) -> None:
        meta = get_category_meta(self.category)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(24, 16))

        ctk.CTkButton(
            header, text="🗺️ Categories", font=theme.font_body(14), width=120, height=36,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._on_back,
        ).pack(side="left")

        ctk.CTkLabel(
            header, text=f"{meta.icon} {meta.title}", font=theme.font_title(26),
            text_color=meta.color,
        ).pack(side="left", padx=20)

    def _build_levels(self) -> None:
        engine = self.app.lesson_engine
        meta = get_category_meta(self.category)
        badge_text_color = contrasting_text_color(meta.color)
        completed_ids = set(self.app.progress.get_completed_lesson_ids())
        stars_by_lesson = self.app.progress.get_stars_by_lesson()
        lessons = engine.lessons_in_category(self.category)

        for lesson in lessons:
            is_completed = lesson.id in completed_ids
            is_unlocked = engine.is_unlocked(lesson, completed_ids)
            stars = stars_by_lesson.get(lesson.id, 0)

            if is_completed:
                status_text = f"✅ Completed  {'⭐' * stars}"
                status_color = theme.COLOR_SUCCESS
                button_text = "▶ REPLAY"
                enabled = True
            elif is_unlocked:
                status_text = "🔓 Ready to play!"
                status_color = theme.COLOR_PRIMARY
                button_text = "▶ PLAY"
                enabled = True
            else:
                status_text = "🔒 Locked — finish the level above first"
                status_color = theme.COLOR_TEXT_MUTED
                button_text = "🔒 LOCKED"
                enabled = False

            card = ctk.CTkFrame(self.body, fg_color=theme.COLOR_CARD, corner_radius=16)
            card.pack(fill="x", pady=8)

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=20, pady=(16, 2))

            # A colored badge (the category's color) makes the level number
            # recognizable by color alone, Scratch-block style.
            ctk.CTkLabel(
                top_row, text=str(lesson.category_level), font=theme.font_heading(16),
                text_color=badge_text_color, fg_color=meta.color,
                corner_radius=16, width=32, height=32,
            ).pack(side="left", padx=(0, 10))

            ctk.CTkLabel(
                top_row, text=lesson.title, font=theme.font_heading(18), text_color=theme.COLOR_TEXT,
            ).pack(side="left")

            ctk.CTkLabel(
                card, text=status_text, font=theme.font_body(14), text_color=status_color,
            ).pack(anchor="w", padx=20, pady=(0, 10))

            ctk.CTkButton(
                card, text=button_text, font=theme.font_button(16), width=160, height=44,
                fg_color=theme.COLOR_SUCCESS if enabled else theme.COLOR_TEXT_MUTED,
                hover_color=theme.COLOR_SUCCESS_HOVER if enabled else theme.COLOR_TEXT_MUTED,
                state="normal" if enabled else "disabled",
                command=lambda lesson_id=lesson.id: self.app.show_lesson(lesson_id),
            ).pack(anchor="w", padx=20, pady=(0, 16))

    def _on_back(self) -> None:
        self.app.show_category_map()
