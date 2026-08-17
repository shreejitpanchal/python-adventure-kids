"""The Quiz category: pick how many questions to answer, then a randomized
multiple-choice run through that many, one question at a time, ending in a
score summary scored out of however many were picked.

Every question has exactly 4 options (content/quiz/quiz_questions.yaml),
so the option buttons are built once and reused across questions rather
than rebuilt each time -- the same mutate-in-place-then-page.update()
shape as app/ui/lesson_screen_flet.py's _LessonController.
"""
from __future__ import annotations

import flet as ft

from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color
from app.ui.theme_flet import scaled

_OPTION_COUNT = 4
_RESULTS_CARD_COLOR = "#FFF3D0"
_COUNT_CHOICES = [5, 10, 15, 20, 25, 30, 50]


def build_quiz_view(page: ft.Page, state: AppState) -> ft.View:
    return _QuizController(page, state).build_view()


class _QuizController:
    def __init__(self, page: ft.Page, state: AppState) -> None:
        self.page = page
        self.state = state
        self.theme = state.theme
        self.scale = state.font_scale

        # The question count is picked on the setup card before a session
        # starts -- see _on_pick_count().
        self.questions: list = []
        self.total = 0
        self.index = 0
        self.score = 0
        self.answered = False
        # concept_tags from every question missed this session -- purely
        # in-memory, discarded once a new session starts; no DB change
        # needed for this (see _show_results()'s "practice these next").
        self.missed_tags: set[str] = set()

    def _fs(self, base_size: int) -> int:
        """Scaled font size -- see AppState.font_scale / app/ui/theme_flet.py."""
        return scaled(base_size, self.scale)

    # -- layout -----------------------------------------------------------------
    def build_view(self) -> ft.View:
        theme = self.theme

        header = ft.Row(
            [
                ft.Button(
                    "🏠 Menu", on_click=self._on_menu, height=48,
                    style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
                ),
                ft.Text("❓ Quiz", size=self._fs(26), weight=ft.FontWeight.BOLD, color=theme.primary),
            ],
            spacing=16,
        )

        self.setup_card = self._build_setup_card()

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
        self.question_card.visible = False

        # The results card's cream background is fixed regardless of the
        # active theme (a deliberate always-celebratory look), so its text
        # must be too -- theme.text is tuned for dark themes' own dark
        # background and turns near-invisible on this light card (#2547).
        self.results_text = ft.Text(
            "", size=self._fs(22), weight=ft.FontWeight.BOLD, color=contrasting_text_color(_RESULTS_CARD_COLOR),
        )
        results_card_text_color = contrasting_text_color(_RESULTS_CARD_COLOR)
        self.practice_heading = ft.Text(
            "💡 Practice these next:", size=self._fs(15), weight=ft.FontWeight.BOLD, color=results_card_text_color, visible=False,
        )
        self.practice_row = ft.Row([], spacing=8, wrap=True, alignment=ft.MainAxisAlignment.CENTER)
        self.results_card = ft.Container(
            content=ft.Column(
                [
                    self.results_text,
                    self.practice_heading,
                    self.practice_row,
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
            bgcolor=_RESULTS_CARD_COLOR, border_radius=18, padding=24, visible=False,
        )

        return ft.View(
            route="/quiz",
            bgcolor=theme.bg,
            scroll=ft.ScrollMode.AUTO,
            padding=24,
            controls=[header, self.setup_card, self.question_card, self.results_card],
        )

    def _build_setup_card(self) -> ft.Control:
        available = len(self.state.quiz_engine)
        buttons = [
            ft.Button(
                f"{n}", on_click=lambda _e, n=n: self._on_pick_count(n), width=90, height=56,
                style=ft.ButtonStyle(bgcolor=self.theme.primary, color="#FFFFFF"),
            )
            for n in _COUNT_CHOICES
            if n <= available
        ]
        return self._card("❓ How many questions?", [
            ft.Text(f"{available} questions available -- pick how many to answer:", size=self._fs(13), color=self.theme.text_muted),
            ft.Row(buttons, wrap=True, spacing=10, run_spacing=10),
        ])

    def _card(self, title: str, children: list[ft.Control]) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                [ft.Text(title, size=self._fs(18), weight=ft.FontWeight.BOLD, color=self.theme.text), *children],
                spacing=10,
            ),
            bgcolor=self.theme.card, border_radius=18, padding=20,
        )

    def _make_option_button(self, index: int) -> ft.Button:
        # Button has no `text` property in this Flet version -- only
        # `content` (a string is wrapped into a Text control, but only once,
        # at construction). Keep our own reference to that Text so later
        # renders can mutate `.value`/`.color` on it directly, the same
        # live-property pattern used for every other label on this screen.
        label = ft.Text("", size=self._fs(15))
        self.option_labels.append(label)
        return ft.Button(
            content=label, on_click=lambda _e, i=index: self._on_select(i), height=56, width=560,
            style=ft.ButtonStyle(bgcolor=self.theme.bg),
        )

    # -- setup ----------------------------------------------------------------
    def _on_pick_count(self, count: int) -> None:
        self.questions = self.state.quiz_engine.start_session(count)
        self.total = len(self.questions)
        self.index = 0
        self.score = 0
        self.missed_tags = set()
        self.setup_card.visible = False
        self.question_card.visible = True
        self._render_question()

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
        else:
            self.missed_tags.update(question.concept_tags)

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

    def _show_results(self) -> None:
        self.state.progress.record_quiz_attempt(self.score, self.total)
        percent = round(100 * self.score / self.total)
        self.results_text.value = f"🏁 You scored {self.score} / {self.total} ({percent}%)"

        completed_ids = self.state.progress.get_completed_lesson_ids()
        suggestions = self.state.lesson_engine.recommend_practice_for_tags(self.missed_tags, completed_ids)
        self.practice_heading.visible = bool(suggestions)
        self.practice_row.controls = [
            ft.Button(
                lesson.title, height=40,
                on_click=lambda _e, lesson_id=lesson.id: self.page.go(f"/lesson/{lesson_id}"),
                style=ft.ButtonStyle(bgcolor=self.theme.warning, color="#FFFFFF"),
            )
            for lesson in suggestions
        ]

        self.question_card.visible = False
        self.results_card.visible = True
        self.page.update()

    def _on_play_again(self, e) -> None:
        # Back to the setup card rather than silently reusing the last
        # question count -- lets the child pick a different length next time.
        self.results_card.visible = False
        self.setup_card.visible = True
        self.page.update()

    def _on_menu(self, e) -> None:
        self.page.go("/dashboard")
