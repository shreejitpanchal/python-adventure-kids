"""A course chapter's quiz item: a fixed-length multiple-choice run through
questions filtered to that chapter's topic (via Lesson.concept_tags),
passing at >=70% to complete the item -- see app/engine/course_status.py.

Reuses quiz_screen.py's question/results-card structure, but skips its
"pick how many questions" setup card -- the question count and topic are
both fixed by the course lesson itself, not chosen by the child.
"""
from __future__ import annotations

import customtkinter as ctk

from app.engine.categories import get_category_meta
from app.engine.course_status import maybe_award_course_badge
from app.ui import theme
from app.ui.color_utils import contrasting_text_color

_OPTION_COUNT = 4
_QUESTION_COUNT = 8
_PASS_PERCENT = 70
_RESULTS_CARD_COLOR = "#FFF3D0"


class CourseQuizScreen(ctk.CTkFrame):
    def __init__(self, app, lesson_id: str) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app
        self.lesson = app.lesson_engine.get(lesson_id)

        self.questions = app.quiz_engine.start_session_for_tags(self.lesson.concept_tags, count=_QUESTION_COUNT)
        self.total = len(self.questions)
        self.index = 0
        self.score = 0
        self.answered = False

        self._build_header()

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self._build_question_card()
        self._build_results_card()
        self.results_card.pack_forget()

        self._render_question()

    # -- header -----------------------------------------------------------------
    def _build_header(self) -> None:
        meta = get_category_meta(self.lesson.category)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(24, 10))

        ctk.CTkButton(
            header, text="🎓 Python Learning", font=theme.font_body(14), width=160, height=36,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._on_back,
        ).pack(side="left")

        ctk.CTkLabel(
            header, text=f"{meta.icon} {self.lesson.title}", font=theme.font_title(22),
            text_color=meta.color,
        ).pack(side="left", padx=20)

    def _card(self, parent, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=theme.COLOR_CARD, corner_radius=18)
        card.pack(fill="x", pady=10)
        ctk.CTkLabel(
            card, text=title, font=theme.font_heading(18), text_color=theme.COLOR_TEXT,
        ).pack(anchor="w", padx=24, pady=(18, 6))
        return card

    # -- question flow ------------------------------------------------------
    def _build_question_card(self) -> None:
        self.question_card = self._card(self.body, "❓ Question")

        self.progress_label = ctk.CTkLabel(
            self.question_card, text="", font=theme.font_body(14), text_color=theme.COLOR_TEXT_MUTED,
        )
        self.progress_label.pack(anchor="w", padx=24, pady=(0, 6))

        self.question_label = ctk.CTkLabel(
            self.question_card, text="", font=theme.font_heading(18), text_color=theme.COLOR_TEXT,
            justify="left", wraplength=820,
        )
        self.question_label.pack(anchor="w", padx=24, pady=(0, 14))

        self.option_buttons: list[ctk.CTkButton] = []
        for i in range(_OPTION_COUNT):
            button = ctk.CTkButton(
                self.question_card, text="", font=theme.font_body(15), anchor="w",
                height=48, corner_radius=12,
                fg_color=theme.COLOR_BG, hover_color=theme.COLOR_TEXT_MUTED, text_color=theme.COLOR_TEXT,
                command=lambda idx=i: self._on_select(idx),
            )
            button.pack(fill="x", padx=24, pady=6)
            self.option_buttons.append(button)

        self.feedback_label = ctk.CTkLabel(
            self.question_card, text="", font=theme.font_body(14), justify="left", wraplength=820,
        )
        self.feedback_label.pack(anchor="w", padx=24, pady=(6, 6))

        self.next_button = ctk.CTkButton(
            self.question_card, text="Next ➜", font=theme.font_button(16), width=160, height=44,
            fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
            command=self._on_next,
        )
        self.next_button.pack(anchor="w", padx=24, pady=(0, 20))
        self.next_button.pack_forget()

    def _render_question(self) -> None:
        question = self.questions[self.index]

        self.progress_label.configure(text=f"Question {self.index + 1} of {self.total}  ·  Score: {self.score}")
        self.question_label.configure(text=question.question)

        for i, button in enumerate(self.option_buttons):
            button.configure(
                text=question.options[i], state="normal",
                fg_color=theme.COLOR_BG, hover_color=theme.COLOR_TEXT_MUTED, text_color=theme.COLOR_TEXT,
            )

        self.feedback_label.configure(text="")
        self.next_button.pack_forget()
        self.answered = False

    def _on_select(self, index: int) -> None:
        if self.answered:
            return
        self.answered = True

        question = self.questions[self.index]
        correct = index == question.correct
        if correct:
            self.score += 1

        for i, button in enumerate(self.option_buttons):
            button.configure(state="disabled")
            if i == question.correct:
                button.configure(fg_color=theme.COLOR_SUCCESS, text_color="#FFFFFF")
            elif i == index:
                button.configure(fg_color=theme.COLOR_DANGER, text_color="#FFFFFF")

        prefix = "✅ Correct! " if correct else "❌ Not quite. "
        self.feedback_label.configure(
            text=prefix + question.explanation,
            text_color=theme.COLOR_SUCCESS if correct else theme.COLOR_DANGER,
        )

        self.next_button.configure(text="Next ➜" if self.index + 1 < self.total else "See Results 🏁")
        self.next_button.pack(anchor="w", padx=24, pady=(0, 20))
        self.progress_label.configure(text=f"Question {self.index + 1} of {self.total}  ·  Score: {self.score}")

    def _on_next(self) -> None:
        self.index += 1
        if self.index >= self.total:
            self._show_results()
        else:
            self._render_question()

    # -- results ------------------------------------------------------------
    def _build_results_card(self) -> None:
        self.results_card = ctk.CTkFrame(self.body, fg_color=_RESULTS_CARD_COLOR, corner_radius=18)

        self.results_label = ctk.CTkLabel(
            self.results_card, text="", font=theme.font_title(24),
            text_color=contrasting_text_color(_RESULTS_CARD_COLOR),
        )
        self.results_label.pack(pady=(24, 16))

        self.results_button_row = ctk.CTkFrame(self.results_card, fg_color="transparent")
        self.results_button_row.pack(pady=(0, 24))

    def _show_results(self) -> None:
        percent = round(100 * self.score / self.total) if self.total else 0
        self.app.progress.record_quiz_attempt(self.score, self.total)
        passed = percent >= _PASS_PERCENT

        for child in self.results_button_row.winfo_children():
            child.destroy()

        if passed:
            self.app.progress.complete_lesson(self.lesson.id, self.lesson.reward_stars)
            maybe_award_course_badge(self.app.lesson_engine, self.app.progress)
            self.results_label.configure(
                text=f"🏁 You scored {self.score}/{self.total} ({percent}%) — Passed!",
            )
            ctk.CTkButton(
                self.results_button_row, text="✅ Continue", font=theme.font_button(18), width=180, height=52,
                fg_color=theme.COLOR_SUCCESS, hover_color=theme.COLOR_SUCCESS_HOVER,
                command=self._on_back,
            ).pack(side="left", padx=(0, 10))
        else:
            self.results_label.configure(
                text=f"🏁 You scored {self.score}/{self.total} ({percent}%) — Try again to pass!",
            )
            ctk.CTkButton(
                self.results_button_row, text="🔁 Try Again", font=theme.font_button(18), width=180, height=52,
                fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
                command=self._on_retry,
            ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            self.results_button_row, text="🎓 Chapter", font=theme.font_button(18), width=140, height=52,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._on_back,
        ).pack(side="left")

        self.question_card.pack_forget()
        self.results_card.pack(fill="x", pady=10)

    def _on_retry(self) -> None:
        self.questions = self.app.quiz_engine.start_session_for_tags(self.lesson.concept_tags, count=_QUESTION_COUNT)
        self.total = len(self.questions)
        self.index = 0
        self.score = 0
        self.results_card.pack_forget()
        self.question_card.pack(fill="x", pady=10)
        self._render_question()

    def _on_back(self) -> None:
        self.app.show_course_chapter(self.lesson.category)
