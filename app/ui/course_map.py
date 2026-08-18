"""The "🎓 Python Learning" course dashboard: an XP/progress-bar header
(styled after dashboard.py's _build_xp_hud/_stat_pill) above a 2-column grid
of chapter cards (styled after settings_screen.py's theme-picker grid).

Chapters are never locked -- every chapter is always browsable; only the 3
items *within* a chapter gate in order (see course_chapter.py)."""
from __future__ import annotations

import customtkinter as ctk

from app.engine.categories import get_category_meta
from app.engine.course_status import compute_course_status
from app.ui import theme
from app.ui.color_utils import contrasting_text_color


class CourseMapFrame(ctk.CTkFrame):
    def __init__(self, app) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app
        self.status = compute_course_status(app.lesson_engine, app.progress)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self._build_header(self.scroll)
        self._build_hud(self.scroll)
        self._build_chapter_grid(self.scroll)

    def _build_header(self, parent) -> None:
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(24, 10))

        ctk.CTkButton(
            header, text="🏠 Menu", font=theme.font_body(14), width=100, height=36,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._on_menu,
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="🎓 Python Learning", font=theme.font_title(26),
            text_color=theme.COLOR_PRIMARY,
        ).pack(side="left", padx=20)

    def _build_hud(self, parent) -> None:
        hud = ctk.CTkFrame(parent, fg_color=theme.COLOR_CARD, corner_radius=16)
        hud.pack(fill="x", padx=30, pady=(0, 20))

        ratio = self.status.items_done / self.status.items_total if self.status.items_total else 0.0
        progress_bar = ctk.CTkProgressBar(hud, height=18, corner_radius=9, progress_color=theme.COLOR_SUCCESS)
        progress_bar.pack(fill="x", padx=24, pady=(20, 4))
        progress_bar.set(ratio)

        ctk.CTkLabel(
            hud, text=f"{self.status.items_done}/{self.status.items_total} lessons complete",
            font=theme.font_body(12), text_color=theme.COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=24, pady=(0, 14))

        stats_row = ctk.CTkFrame(hud, fg_color="transparent")
        stats_row.pack(fill="x", padx=16, pady=(0, 16))

        self._stat_pill(stats_row, "⭐", f"{self.status.stars_earned} XP")
        self._stat_pill(stats_row, "📘", f"{self.status.items_done}/{self.status.items_total} lessons done")
        self._stat_pill(stats_row, "📖", f"{len(self.status.chapters)} chapters")

    def _stat_pill(self, parent, icon: str, text: str) -> None:
        pill = ctk.CTkFrame(parent, fg_color=theme.COLOR_BG, corner_radius=14)
        pill.pack(side="left", padx=8, pady=4)
        ctk.CTkLabel(
            pill, text=f"{icon}  {text}", font=theme.font_body(14),
            text_color=theme.COLOR_TEXT,
        ).pack(padx=14, pady=8)

    def _build_chapter_grid(self, parent) -> None:
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x", padx=30, pady=(0, 30))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        for index, chapter in enumerate(self.status.chapters):
            row, col = divmod(index, 2)
            self._build_chapter_card(grid, chapter, index + 1, row, col)

    def _build_chapter_card(self, parent, chapter, chapter_number: int, row: int, col: int) -> None:
        meta = get_category_meta(chapter.category)
        badge_text_color = contrasting_text_color(meta.color)

        card = ctk.CTkFrame(parent, fg_color=theme.COLOR_CARD, corner_radius=18)
        card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            top_row, text=str(chapter_number), font=theme.font_heading(16),
            text_color=badge_text_color, fg_color=meta.color,
            corner_radius=16, width=32, height=32,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            top_row, text=meta.title, font=theme.font_heading(17), text_color=theme.COLOR_TEXT,
            wraplength=200, justify="left",
        ).pack(side="left")

        status_text = (
            "✅ Chapter complete!" if chapter.completed_count == chapter.total_count
            else f"{chapter.completed_count}/{chapter.total_count} items"
        )
        status_color = theme.COLOR_SUCCESS if chapter.completed_count == chapter.total_count else theme.COLOR_TEXT_MUTED
        ctk.CTkLabel(
            card, text=status_text, font=theme.font_body(13), text_color=status_color,
        ).pack(anchor="w", padx=20, pady=(0, 16))

        ctk.CTkButton(
            card, text="▶ Open Chapter", font=theme.font_button(14), height=38,
            fg_color=meta.color, hover_color=theme.COLOR_PRIMARY_HOVER,
            text_color=badge_text_color,
            command=lambda category=chapter.category: self._on_open_chapter(category),
        ).pack(fill="x", padx=20, pady=(0, 16))

    def _on_open_chapter(self, category: str) -> None:
        self.app.show_course_chapter(category)

    def _on_menu(self) -> None:
        self.app.show_hub()
