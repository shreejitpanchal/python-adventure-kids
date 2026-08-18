"""One course chapter's items: "1. What is X?", "2. Your Sample Program",
"3. Quiz" -- gated in order within each topic group via
is_topic_item_unlocked() (topic-scoped, so sibling topics like Tuples and
Sets never block each other), restyled for the course dashboard look. A
chapter with only one implicit topic (topic="" on every lesson) renders
identically to a flat 3-item list -- no topic heading shown."""
from __future__ import annotations

import customtkinter as ctk

from app.engine.categories import get_category_meta, get_topic_icon
from app.engine.course_status import compute_course_status, is_topic_item_unlocked
from app.ui import theme
from app.ui.color_utils import contrasting_text_color

_ITEM_LABELS = ["1. What is it?", "2. Your Sample Program", "3. Quiz"]


class CourseChapterFrame(ctk.CTkFrame):
    def __init__(self, app, category: str) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app
        self.category = category

        self._build_header()

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self._build_topics()

    def _build_header(self) -> None:
        meta = get_category_meta(self.category)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(24, 16))

        ctk.CTkButton(
            header, text="🎓 Python Learning", font=theme.font_body(14), width=160, height=36,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._on_back,
        ).pack(side="left")

        ctk.CTkLabel(
            header, text=f"{meta.icon} {meta.title}", font=theme.font_title(24),
            text_color=meta.color,
        ).pack(side="left", padx=20)

    def _build_topics(self) -> None:
        status = compute_course_status(self.app.lesson_engine, self.app.progress)
        chapter = next(c for c in status.chapters if c.category == self.category)
        completed_ids = set(self.app.progress.get_completed_lesson_ids())
        meta = get_category_meta(self.category)

        for topic in chapter.topics:
            if topic.topic:
                icon = get_topic_icon(topic.topic)
                heading = f"{icon} {topic.topic}".strip()
                topic_header = ctk.CTkFrame(self.body, fg_color="transparent")
                topic_header.pack(fill="x", pady=(16, 4))
                ctk.CTkLabel(
                    topic_header, text=heading, font=theme.font_heading(18), text_color=meta.color,
                ).pack(side="left")
                ctk.CTkLabel(
                    topic_header, text=f"{topic.completed_count}/{topic.total_count}",
                    font=theme.font_body(13), text_color=theme.COLOR_TEXT_MUTED,
                ).pack(side="left", padx=(10, 0))

            for index, lesson in enumerate(topic.items):
                self._build_item_card(lesson, index, topic.items, completed_ids, meta)

    def _build_item_card(self, lesson, index: int, topic_items: list, completed_ids: set, meta) -> None:
        badge_text_color = contrasting_text_color(meta.color)
        is_completed = lesson.id in completed_ids
        is_unlocked = is_topic_item_unlocked(lesson, topic_items, completed_ids)
        label = _ITEM_LABELS[index] if index < len(_ITEM_LABELS) else lesson.title

        if is_completed:
            status_text = "✅ Completed"
            button_text = "▶ REPLAY"
            enabled = True
        elif is_unlocked:
            status_text = "🔓 Ready to play!"
            button_text = "🧩 QUIZ" if lesson.is_quiz else "▶ PLAY"
            enabled = True
        else:
            status_text = "🔒 Locked — finish the item above first"
            button_text = "🔒 LOCKED"
            enabled = False

        card = ctk.CTkFrame(self.body, fg_color=theme.COLOR_CARD, corner_radius=16)
        card.pack(fill="x", pady=8)

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(16, 2))

        ctk.CTkLabel(
            top_row, text=str(index + 1), font=theme.font_heading(16),
            text_color=badge_text_color, fg_color=meta.color,
            corner_radius=16, width=32, height=32,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            top_row, text=f"{label} — {lesson.title}", font=theme.font_heading(17),
            text_color=theme.COLOR_TEXT,
        ).pack(side="left")

        status_color = theme.COLOR_SUCCESS if is_completed else (
            theme.COLOR_PRIMARY if is_unlocked else theme.COLOR_TEXT_MUTED
        )
        ctk.CTkLabel(
            card, text=status_text, font=theme.font_body(14), text_color=status_color,
        ).pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkButton(
            card, text=button_text, font=theme.font_button(16), width=160, height=44,
            fg_color=theme.COLOR_SUCCESS if enabled else theme.COLOR_TEXT_MUTED,
            hover_color=theme.COLOR_SUCCESS_HOVER if enabled else theme.COLOR_TEXT_MUTED,
            state="normal" if enabled else "disabled",
            command=lambda lesson_id=lesson.id: self.app.show_lesson_or_quiz(lesson_id),
        ).pack(anchor="w", padx=20, pady=(0, 16))

    def _on_back(self) -> None:
        self.app.show_course_map()
