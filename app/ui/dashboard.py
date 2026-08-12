"""Main screen: greets the child, shows level/progress, starts today's lesson,
and lists completed missions on the left so the child can replay any of them.

The whole thing is wrapped in a scrollable frame, since content height varies
with font/DPI scaling and grows as more lessons are completed -- this keeps
the Continue button reachable no matter what."""
from __future__ import annotations

import customtkinter as ctk

from app.engine.categories import get_category_meta
from app.ui import theme
from app.ui.assets import make_ctk_icon
from app.ui.color_utils import contrasting_text_color, darken


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, app) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self._build_header(self.scroll)
        self._build_body(self.scroll)
        self._build_footer(self.scroll)

    def _build_header(self, parent) -> None:
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=40, pady=(30, 10))

        # Kept as an attribute so the underlying image isn't garbage-collected.
        self.icon_image = make_ctk_icon(size=40)
        ctk.CTkLabel(
            header, text=" Python Adventure", image=self.icon_image, compound="left",
            font=theme.font_title(30), text_color=theme.COLOR_PRIMARY,
        ).pack(side="left")

        ctk.CTkButton(
            header, text="👋 Parent Area", font=theme.font_body(13), width=140, height=36,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._open_parent_area,
        ).pack(side="right")

        ctk.CTkButton(
            header, text="🗺️ Categories", font=theme.font_body(13), width=140, height=36,
            fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
            command=self._open_category_map,
        ).pack(side="right", padx=(0, 10))

        name = self.app.settings.child_name or "Explorer"
        ctk.CTkLabel(
            parent, text=f"Welcome back, {name}!", font=theme.font_heading(20),
            text_color=theme.COLOR_TEXT,
        ).pack(anchor="w", padx=44, pady=(0, 20))

    def _build_body(self, parent) -> None:
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=10)

        self._build_missions_sidebar(container)
        self._build_mission_card(container)

    # -- left sidebar: completed missions, replayable -------------------------
    def _build_missions_sidebar(self, parent) -> None:
        sidebar = ctk.CTkFrame(parent, fg_color=theme.COLOR_CARD, corner_radius=20, width=260)
        sidebar.pack(side="left", fill="y", padx=(0, 16))

        ctk.CTkLabel(
            sidebar, text="✅ Completed Missions", font=theme.font_heading(16),
            text_color=theme.COLOR_TEXT, wraplength=220, justify="left",
        ).pack(anchor="w", padx=16, pady=(20, 10))

        engine = self.app.lesson_engine
        completed_ids = set(self.app.progress.get_completed_lesson_ids())
        stars_by_lesson = self.app.progress.get_stars_by_lesson()
        completed_lessons = [lesson for lesson in engine.all_in_order() if lesson.id in completed_ids]

        if not completed_lessons:
            ctk.CTkLabel(
                sidebar,
                text="Finish your first mission to see it here — then you can replay it anytime!",
                font=theme.font_body(12), text_color=theme.COLOR_TEXT_MUTED,
                wraplength=210, justify="left",
            ).pack(anchor="w", padx=16, pady=(0, 16))
            return

        # A plain frame, not another CTkScrollableFrame -- nesting scrollable
        # frames causes cross-talk in CTk's own wheel handling (even a
        # correctly-isolated custom handler can't fully suppress it, since
        # CTk's native per-frame handlers stay registered too). The outer
        # dashboard scroll (see __init__) already reveals any overflow here,
        # and its mousewheel binding now actually works.
        list_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        list_frame.pack(fill="x", padx=8, pady=(0, 12))

        for lesson in completed_lessons:
            stars = stars_by_lesson.get(lesson.id, 0)
            meta = get_category_meta(lesson.category)
            ctk.CTkButton(
                list_frame, text=f"{lesson.title}\n{'⭐' * stars}",
                font=theme.font_body(13), anchor="w",
                fg_color=meta.color, hover_color=darken(meta.color),
                text_color=contrasting_text_color(meta.color), height=52, corner_radius=10,
                command=lambda lesson_id=lesson.id: self._on_replay(lesson_id),
            ).pack(fill="x", pady=4, padx=4)

    def _on_replay(self, lesson_id: str) -> None:
        self.app.show_lesson(lesson_id)

    # -- right side: today's mission --------------------------------------------
    def _build_mission_card(self, parent) -> None:
        summary = self.app.progress.get_summary()
        engine = self.app.lesson_engine

        completed_ids = self.app.progress.get_completed_lesson_ids()
        self.current_lesson = engine.resolve_current(completed_ids, summary.current_lesson_id)
        already_completed = self.current_lesson.id in completed_ids

        card = ctk.CTkFrame(parent, fg_color=theme.COLOR_CARD, corner_radius=20)
        card.pack(side="left", fill="both", expand=True)

        stats_row = ctk.CTkFrame(card, fg_color="transparent")
        stats_row.pack(fill="x", padx=30, pady=(24, 10))

        self._stat_pill(stats_row, "⭐", f"{summary.total_stars} stars")
        self._stat_pill(stats_row, "🏆", f"Level {summary.level}")
        self._stat_pill(stats_row, "🔥", f"{summary.streak_days} day streak")
        self._stat_pill(stats_row, "🎖️", f"{summary.badges_earned} badges")

        ctk.CTkLabel(
            card, text="Today's Mission", font=theme.font_body(14),
            text_color=theme.COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=32, pady=(20, 0))

        ctk.CTkLabel(
            card, text=self.current_lesson.title, font=theme.font_heading(26),
            text_color=theme.COLOR_TEXT,
        ).pack(anchor="w", padx=32, pady=(4, 4))

        if already_completed:
            ctk.CTkLabel(
                card, text="✅ Completed — replay anytime!", font=theme.font_body(14),
                text_color=theme.COLOR_SUCCESS,
            ).pack(anchor="w", padx=32, pady=(0, 16))
        else:
            ctk.CTkLabel(
                card, text=self.current_lesson.objective, font=theme.font_body(14),
                text_color=theme.COLOR_TEXT_MUTED, wraplength=700, justify="left",
            ).pack(anchor="w", padx=32, pady=(0, 16))

        total_lessons = max(len(engine.main_path_lessons()), 1)
        progress_bar = ctk.CTkProgressBar(
            card, height=18, corner_radius=9, progress_color=theme.COLOR_STAR,
        )
        progress_bar.pack(fill="x", padx=32, pady=(0, 10))
        progress_bar.set(min(summary.lessons_completed / total_lessons, 1.0))

        button_text = "▶ REPLAY" if already_completed else "▶ CONTINUE"
        ctk.CTkButton(
            card, text=button_text, font=theme.font_button(24), width=280, height=64,
            fg_color=theme.COLOR_SUCCESS, hover_color=theme.COLOR_SUCCESS_HOVER,
            command=self._on_continue,
        ).pack(pady=(20, 30))

    def _stat_pill(self, parent, icon: str, text: str) -> None:
        pill = ctk.CTkFrame(parent, fg_color=theme.COLOR_BG, corner_radius=14)
        pill.pack(side="left", padx=8, pady=4)
        ctk.CTkLabel(
            pill, text=f"{icon}  {text}", font=theme.font_body(15),
            text_color=theme.COLOR_TEXT,
        ).pack(padx=14, pady=8)

    def _build_footer(self, parent) -> None:
        ctk.CTkLabel(
            parent, text="More lessons are on their way! 🚀", font=theme.font_body(13),
            text_color=theme.COLOR_TEXT_MUTED,
        ).pack(pady=16)

    def _on_continue(self) -> None:
        self.app.show_lesson(self.current_lesson.id)

    def _open_parent_area(self) -> None:
        from app.parent.dashboard import open_parent_area

        open_parent_area(self.app)

    def _open_category_map(self) -> None:
        self.app.show_category_map()
