"""The Quiz category: a randomized multiple-choice run through the whole
question bank, one question at a time, ending in a score summary.

Every question has exactly 4 options (content/quiz/quiz_questions.yaml),
so the option buttons are built once and reused across questions rather
than rebuilt each time -- the same mutate-in-place-then-page.update()
shape as app/ui/lesson_screen_flet.py's _LessonController.
"""
from __future__ import annotations

import flet as ft

from app.ui.app_state_flet import AppState

_OPTION_COUNT = 4


def build_quiz_view(page: ft.Page, state: AppState) -> ft.View:
    return _QuizController(page, state).build_view()


class _QuizController:
    def __init__(self, page: ft.Page, state: AppState) -> None:
        self.page = page
        self.state = state
        self.theme = state.theme

        self.questions = state.quiz_engine.start_session()
        self.total = len(self.questions)
        self.index = 0
        self.score = 0
        self.answered = False

    # -- layout -----------------------------------------------------------------
    def build_view(self) -> ft.View:
        theme = self.theme

        header = ft.Row(
            [
                ft.Button(
                    "🏠 Menu", on_click=self._on_menu, height=48,
                    style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
                ),
                ft.Text("❓ Quiz", size=26, weight=ft.FontWeight.BOLD, color=theme.primary),
            ],
            spacing=16,
        )

        self.progress_text = ft.Text("", size=14, color=theme.text_muted)
        self.question_text = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=theme.text)
        self.option_buttons = [self._make_option_button(i) for i in range(_OPTION_COUNT)]
        self.feedback_text = ft.Text("", size=14)
        self.next_button = ft.Button(
            "Next ➜", on_click=self._on_next, visible=False, height=48,
            style=ft.ButtonStyle(bgcolor=theme.primary, color="#FFFFFF"),
        )

        self.question_card = self._card("❓ Question", [
            self.progress_text,
            self.question_text,
            ft.Column(self.option_buttons, spacing=10),
            self.feedback_text,
            self.next_button,
        ])

        self.results_text = ft.Text("", size=22, weight=ft.FontWeight.BOLD, color=theme.text)
        self.results_card = ft.Container(
            content=ft.Column(
                [
                    self.results_text,
                    ft.Row(
                        [
                            ft.Button(
                                "🔁 Play Again", on_click=self._on_play_again, height=52,
                                style=ft.ButtonStyle(bgcolor=theme.success, color="#FFFFFF"),
                            ),
                            ft.Button(
                                "🏠 Menu", on_click=self._on_menu, height=52,
                                style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16,
            ),
            bgcolor="#FFF3D0", border_radius=18, padding=24, visible=False,
        )

        self._render_question()

        return ft.View(
            route="/quiz",
            bgcolor=theme.bg,
            scroll=ft.ScrollMode.AUTO,
            padding=24,
            controls=[header, self.question_card, self.results_card],
        )

    def _card(self, title: str, children: list[ft.Control]) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                [ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=self.theme.text), *children],
                spacing=10,
            ),
            bgcolor=self.theme.card, border_radius=18, padding=20,
        )

    def _make_option_button(self, index: int) -> ft.Button:
        return ft.Button(
            "", on_click=lambda _e, i=index: self._on_select(i), height=56, width=560,
            style=ft.ButtonStyle(bgcolor=self.theme.bg, color=self.theme.text),
        )

    # -- question flow ------------------------------------------------------
    def _render_question(self) -> None:
        theme = self.theme
        question = self.questions[self.index]

        self.progress_text.value = f"Question {self.index + 1} of {self.total}  ·  Score: {self.score}"
        self.question_text.value = question.question

        for i, button in enumerate(self.option_buttons):
            button.text = question.options[i]
            button.disabled = False
            button.style = ft.ButtonStyle(bgcolor=theme.bg, color=theme.text)

        self.feedback_text.value = ""
        self.next_button.visible = False
        self.answered = False
        self.page.update()

    def _on_select(self, index: int) -> None:
        if self.answered:
            return
        self.answered = True

        theme = self.theme
        question = self.questions[self.index]
        correct = index == question.correct
        if correct:
            self.score += 1

        for i, button in enumerate(self.option_buttons):
            button.disabled = True
            if i == question.correct:
                button.style = ft.ButtonStyle(bgcolor=theme.success, color="#FFFFFF")
            elif i == index:
                button.style = ft.ButtonStyle(bgcolor=theme.danger, color="#FFFFFF")

        prefix = "✅ Correct! " if correct else "❌ Not quite. "
        self.feedback_text.value = prefix + question.explanation
        self.feedback_text.color = theme.success if correct else theme.danger

        self.next_button.text = "Next ➜" if self.index + 1 < self.total else "See Results 🏁"
        self.next_button.visible = True
        self.progress_text.value = f"Question {self.index + 1} of {self.total}  ·  Score: {self.score}"
        self.page.update()

    def _on_next(self, e) -> None:
        self.index += 1
        if self.index >= self.total:
            self._show_results()
        else:
            self._render_question()

    def _show_results(self) -> None:
        self.state.progress.record_quiz_attempt(self.score, self.total)
        percent = round(100 * self.score / self.total)
        self.results_text.value = f"🏁 You scored {self.score} / {self.total} ({percent}%)"
        self.question_card.visible = False
        self.results_card.visible = True
        self.page.update()

    def _on_play_again(self, e) -> None:
        self.questions = self.state.quiz_engine.start_session()
        self.index = 0
        self.score = 0
        self.results_card.visible = False
        self.question_card.visible = True
        self._render_question()

    def _on_menu(self, e) -> None:
        self.page.go("/dashboard")
