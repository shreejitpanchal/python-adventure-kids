"""A course chapter's quiz item: a fixed-length multiple-choice run through
questions filtered to that chapter's topic (via Lesson.concept_tags),
passing at >=70% to complete the item -- see app/engine/course_status.py.

Same controller shape as quiz_screen_flet.py's _QuizController, but skips
its "pick how many questions" setup card -- the question count and topic
are both fixed by the course lesson itself, not chosen by the child.
"""
from __future__ import annotations

import flet as ft

from app.engine.categories import get_category_meta
from app.engine.course_status import maybe_award_course_badge
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color
from app.ui.theme_flet import scaled

_OPTION_COUNT = 4
_QUESTION_COUNT = 8
_PASS_PERCENT = 70
_RESULTS_CARD_COLOR = "#FFF3D0"


def build_course_quiz_view(page: ft.Page, state: AppState, lesson_id: str) -> ft.View:
    return _CourseQuizController(page, state, lesson_id).build_view()


class _CourseQuizController:
    def __init__(self, page: ft.Page, state: AppState, lesson_id: str) -> None:
        self.page = page
        self.state = state
        self.theme = state.theme
        self.scale = state.font_scale
        self.lesson = state.lesson_engine.get(lesson_id)

        self.questions = state.quiz_engine.start_session_for_tags(self.lesson.concept_tags, count=_QUESTION_COUNT)
        self.total = len(self.questions)
        self.index = 0
        self.score = 0
        self.answered = False

    def _fs(self, base_size: int) -> int:
        return scaled(base_size, self.scale)

    # -- layout -----------------------------------------------------------------
    def build_view(self) -> ft.View:
        theme = self.theme
        meta = get_category_meta(self.lesson.category)

        header = ft.Row(
            [
                ft.Button(
                    "🎓 Python Learning", on_click=self._on_back, height=48,
                    style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
                ),
                ft.Text(f"{meta.icon} {self.lesson.title}", size=self._fs(22), weight=ft.FontWeight.BOLD, color=meta.color, expand=True),
            ],
            spacing=16,
        )

        self.progress_text = ft.Text("", size=self._fs(14), color=theme.text_muted)
        self.question_text = ft.Text("", size=self._fs(18), weight=ft.FontWeight.BOLD, color=theme.text)
        self.option_labels: list[ft.Text] = []
        self.option_buttons = [self._make_option_button(i) for i in range(_OPTION_COUNT)]
        self.feedback_text = ft.Text("", size=self._fs(14))
        self.next_label = ft.Text("Next ➜", size=self._fs(16), color="#FFFFFF")
        self.next_button = ft.Button(
            content=self.next_label, on_click=self._on_next, visible=False, height=48,
            style=ft.ButtonStyle(bgcolor=theme.primary),
        )

        self.question_card = self._card("❓ Question", [
            self.progress_text,
            self.question_text,
            ft.Column(self.option_buttons, spacing=10),
            self.feedback_text,
            self.next_button,
        ])

        self.results_text = ft.Text(
            "", size=self._fs(22), weight=ft.FontWeight.BOLD, color=contrasting_text_color(_RESULTS_CARD_COLOR),
        )
        self.results_button_row = ft.Row([], spacing=10)
        self.results_card = ft.Container(
            content=ft.Column(
                [self.results_text, self.results_button_row],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16,
            ),
            bgcolor=_RESULTS_CARD_COLOR, border_radius=18, padding=24, visible=False,
        )

        self.view = ft.View(
            route=f"/course-quiz/{self.lesson.id}",
            bgcolor=theme.bg,
            scroll=ft.ScrollMode.AUTO,
            padding=ft.padding.Padding.only(left=24, top=24, right=24, bottom=80),
            controls=[header, self.question_card, self.results_card],
        )

        self._render_question()
        return self.view

    def _card(self, title: str, children: list[ft.Control]) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                [ft.Text(title, size=self._fs(18), weight=ft.FontWeight.BOLD, color=self.theme.text), *children],
                spacing=10,
            ),
            bgcolor=self.theme.card, border_radius=18, padding=20,
        )

    def _make_option_button(self, index: int) -> ft.Button:
        label = ft.Text("", size=self._fs(15))
        self.option_labels.append(label)
        return ft.Button(
            content=label, on_click=lambda _e, i=index: self._on_select(i), height=56, width=560,
            style=ft.ButtonStyle(bgcolor=self.theme.bg),
        )

    # -- question flow ------------------------------------------------------
    def _render_question(self) -> None:
        theme = self.theme
        question = self.questions[self.index]

        self.progress_text.value = f"Question {self.index + 1} of {self.total}  ·  Score: {self.score}"
        self.question_text.value = question.question

        for i, button in enumerate(self.option_buttons):
            self.option_labels[i].value = question.options[i]
            self.option_labels[i].color = theme.text
            button.disabled = False
            button.style = ft.ButtonStyle(bgcolor=theme.bg)

        self.feedback_text.value = ""
        self.next_button.visible = False
        self.answered = False

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
                button.style = ft.ButtonStyle(bgcolor=theme.success)
                self.option_labels[i].color = "#FFFFFF"
            elif i == index:
                button.style = ft.ButtonStyle(bgcolor=theme.danger)
                self.option_labels[i].color = "#FFFFFF"

        prefix = "✅ Correct! " if correct else "❌ Not quite. "
        self.feedback_text.value = prefix + question.explanation
        self.feedback_text.color = theme.success if correct else theme.danger

        self.next_label.value = "Next ➜" if self.index + 1 < self.total else "See Results 🏁"
        self.next_button.visible = True
        self.progress_text.value = f"Question {self.index + 1} of {self.total}  ·  Score: {self.score}"
        self.page.update()

    def _on_next(self, e) -> None:
        self.index += 1
        if self.index >= self.total:
            self._show_results()
        else:
            self._render_question()
        self.page.update()

    # -- results ------------------------------------------------------------
    def _show_results(self) -> None:
        theme = self.theme
        percent = round(100 * self.score / self.total) if self.total else 0
        self.state.progress.record_quiz_attempt(self.score, self.total)
        passed = percent >= _PASS_PERCENT

        buttons = []
        if passed:
            self.state.progress.complete_lesson(self.lesson.id, self.lesson.reward_stars)
            maybe_award_course_badge(self.state.lesson_engine, self.state.progress)
            self.results_text.value = f"🏁 You scored {self.score}/{self.total} ({percent}%) — Passed!"
            buttons.append(ft.Button(
                "✅ Continue", on_click=self._on_back, height=52,
                style=ft.ButtonStyle(bgcolor=theme.success, color="#FFFFFF"),
            ))
        else:
            self.results_text.value = f"🏁 You scored {self.score}/{self.total} ({percent}%) — Try again to pass!"
            buttons.append(ft.Button(
                "🔁 Try Again", on_click=self._on_retry, height=52,
                style=ft.ButtonStyle(bgcolor=theme.primary, color="#FFFFFF"),
            ))
        buttons.append(ft.Button(
            "🎓 Chapter", on_click=self._on_back, height=52,
            style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
        ))
        self.results_button_row.controls = buttons

        self.question_card.visible = False
        self.results_card.visible = True

    def _on_retry(self, e) -> None:
        self.questions = self.state.quiz_engine.start_session_for_tags(self.lesson.concept_tags, count=_QUESTION_COUNT)
        self.total = len(self.questions)
        self.index = 0
        self.score = 0
        self.results_card.visible = False
        self.question_card.visible = True
        self._render_question()
        self.page.update()

    def _on_back(self, e) -> None:
        self.page.go(f"/course/{self.lesson.category}")
