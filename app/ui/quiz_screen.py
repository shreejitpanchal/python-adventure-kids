"""The Quiz category: pick how many questions to answer, then a randomized
multiple-choice run through that many, one question at a time, ending in a
score summary scored out of however many were picked.

Ported from app/ui/quiz_screen_flet.py -- same controller shape (build
every control once, mutate it in place on each event), just CTk's
pack()/configure() instead of Flet's declarative controls + page.update().
"""
from __future__ import annotations

import customtkinter as ctk

from app.ui import theme
from app.ui.color_utils import contrasting_text_color

_OPTION_COUNT = 4
_RESULTS_CARD_COLOR = "#FFF3D0"
_COUNT_CHOICES = [5, 10, 15, 20, 25, 30, 50]


class QuizScreen(ctk.CTkFrame):
    def __init__(self, app) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app

        # The question count is picked on the setup card before a session
        # starts -- see _on_pick_count().
        self.questions = []
        self.total = 0
        self.index = 0
        self.score = 0
        self.answered = False

        self._build_header()

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self._build_setup_card()
        self._build_question_card()
        self.question_card.pack_forget()
        self._build_results_card()

    # -- header ---------------------------------------------------------------
    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(24, 10))

        ctk.CTkButton(
            header, text="🏠 Menu", font=theme.font_body(14), width=100, height=36,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._on_menu,
        ).pack(side="left")

        ctk.CTkLabel(
            header, text="❓ Quiz", font=theme.font_title(26),
            text_color=theme.COLOR_PRIMARY,
        ).pack(side="left", padx=20)

    def _card(self, title: str) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self.body, fg_color=theme.COLOR_CARD, corner_radius=18)
        card.pack(fill="x", pady=10)
        ctk.CTkLabel(
            card, text=title, font=theme.font_heading(18), text_color=theme.COLOR_TEXT,
        ).pack(anchor="w", padx=24, pady=(18, 6))
        return card

    # -- sections ---------------------------------------------------------------
    def _build_setup_card(self) -> None:
        self.setup_card = self._card("❓ How many questions?")
        available = len(self.app.quiz_engine)

        ctk.CTkLabel(
            self.setup_card, text=f"{available} questions available -- pick how many to answer:",
            font=theme.font_body(13), text_color=theme.COLOR_TEXT_MUTED,
        ).pack(anchor="w", padx=24, pady=(0, 10))

        button_row = ctk.CTkFrame(self.setup_card, fg_color="transparent")
        button_row.pack(anchor="w", padx=24, pady=(0, 20))

        for n in _COUNT_CHOICES:
            if n > available:
                continue
            ctk.CTkButton(
                button_row, text=str(n), font=theme.font_button(16), width=70, height=48,
                fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
                command=lambda n=n: self._on_pick_count(n),
            ).pack(side="left", padx=(0, 8))

    def _build_question_card(self) -> None:
        self.question_card = self._card("❓ Question")

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

    def _build_results_card(self) -> None:
        # The results card's cream background is fixed regardless of the
        # active theme (a deliberate always-celebratory look), so its text
        # must be too -- theme.COLOR_TEXT is tuned for dark themes' own
        # dark background and turns near-invisible on this light card (#2547).
        self.results_card = ctk.CTkFrame(self.body, fg_color=_RESULTS_CARD_COLOR, corner_radius=18)

        self.results_label = ctk.CTkLabel(
            self.results_card, text="", font=theme.font_title(24),
            text_color=contrasting_text_color(_RESULTS_CARD_COLOR),
        )
        self.results_label.pack(pady=(24, 16))

        button_row = ctk.CTkFrame(self.results_card, fg_color="transparent")
        button_row.pack(pady=(0, 24))

        ctk.CTkButton(
            button_row, text="🔁 Play Again", font=theme.font_button(18), width=180, height=52,
            fg_color=theme.COLOR_SUCCESS, hover_color=theme.COLOR_SUCCESS_HOVER,
            command=self._on_play_again,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_row, text="🏠 Menu", font=theme.font_button(18), width=140, height=52,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._on_menu,
        ).pack(side="left")

    # -- setup ------------------------------------------------------------------
    def _on_pick_count(self, count: int) -> None:
        self.questions = self.app.quiz_engine.start_session(count)
        self.total = len(self.questions)
        self.index = 0
        self.score = 0
        self.setup_card.pack_forget()
        self.question_card.pack(fill="x", pady=10)
        self._render_question()

    # -- question flow ------------------------------------------------------
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

    def _show_results(self) -> None:
        self.app.progress.record_quiz_attempt(self.score, self.total)
        percent = round(100 * self.score / self.total)
        self.results_label.configure(text=f"🏁 You scored {self.score} / {self.total} ({percent}%)")
        self.question_card.pack_forget()
        self.results_card.pack(fill="x", pady=10)

    def _on_play_again(self) -> None:
        # Back to the setup card rather than silently reusing the last
        # question count -- lets the child pick a different length next time.
        self.results_card.pack_forget()
        self.setup_card.pack(fill="x", pady=10)

    def _on_menu(self) -> None:
        self.app.show_hub()
