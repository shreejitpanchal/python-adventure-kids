"""The Explain -> Demonstrate -> Try It -> Run -> Result -> Reward lesson flow.

Ported from app/ui/lesson_screen.py, wired to the Phase 2 unified
in-process sandbox (app/sandbox/inprocess_runner.py) instead of the old
subprocess runner. The old CTk version marshalled a background thread's
result back to the UI thread via threading.Thread + app.after(0, ...);
here the same non-blocking shape comes from Flet's own async event
handling via asyncio.to_thread(), which is what "Flet's async model"
means in the re-platform plan.

Graphical lessons (Snake, lessons 16-18) run in-process on the SAME
thread as the async handler itself -- not via asyncio.to_thread -- since
GameCanvas.after() schedules via asyncio.get_running_loop(), which needs
to be Flet's own loop, not a bare worker thread with no loop of its own.
This matches the original design's own assumption that top-level
graphical lesson code returns almost instantly (no blocking loops allowed
-- see disallow_while=True), deferring all animation to scheduled
callbacks instead.
"""
from __future__ import annotations

import asyncio

import flet as ft
import flet.canvas as cv

from app.engine.lesson import Lesson
from app.engine.validator import validate_output
from app.games.game_canvas_flet import GameCanvas
from app.sandbox.errors import extract_error_line_number, translate_error
from app.sandbox.inprocess_runner import ExecutionResult, RunHandle, run_code
from app.ui.app_state_flet import AppState
from app.ui.code_editor_flet import make_code_editor, make_read_only_code_block

_KEY_NAME_MAP = {
    "Arrow Up": "Up", "Arrow Down": "Down", "Arrow Left": "Left", "Arrow Right": "Right",
    "Up": "Up", "Down": "Down", "Left": "Left", "Right": "Right",
    " ": "space", "Space": "space",
}


def build_lesson_view(page: ft.Page, state: AppState, lesson_id: str) -> ft.View:
    theme = state.theme
    lesson = state.lesson_engine.get(lesson_id)

    if lesson is None:
        return ft.View(
            route=f"/lesson/{lesson_id}",
            bgcolor=theme.bg,
            controls=[ft.Text(f"Couldn't find lesson '{lesson_id}'.", color=theme.danger)],
        )

    return _LessonController(page, state, lesson).build_view()


class _LessonController:
    def __init__(self, page: ft.Page, state: AppState, lesson: Lesson) -> None:
        self.page = page
        self.state = state
        self.lesson = lesson
        self.theme = state.theme

        self._running = False
        self._run_handle: RunHandle | None = None
        self._hint_index = 0
        self._lesson_passed = False
        self._current_input_value: str | None = None
        self.input_field: ft.TextField | None = None
        self.game_canvas: GameCanvas | None = None

    # -- layout -----------------------------------------------------------------
    def build_view(self) -> ft.View:
        theme = self.theme
        lesson = self.lesson

        header = ft.Row(
            [
                ft.Button(
                    "🏠 Menu", on_click=self._on_menu, height=48,
                    style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
                ),
                ft.Text(lesson.title, size=22, weight=ft.FontWeight.BOLD, color=theme.primary),
            ],
            spacing=16,
        )

        explanation_card = self._card("📖 Let's Learn", [
            ft.Text(lesson.explanation.strip(), size=15, color=theme.text),
        ])

        example_card = self._card("👀 Example", [
            make_read_only_code_block(lesson.example_code.strip()),
        ])

        challenge_card = self._card("🎯 Try It", [
            ft.Text(lesson.challenge.strip(), size=14, color=theme.text_muted),
        ])

        code_card = self._build_code_card()
        game_panel = self._build_game_panel() if lesson.graphical else None
        output_card = self._build_output_card()
        self._build_reward_card()

        if lesson.graphical:
            self.page.on_keyboard_event = self._on_keyboard_event

        controls = [header, explanation_card, example_card, challenge_card, code_card]
        if game_panel is not None:
            controls.append(game_panel)
        controls.extend([output_card, self.reward_card])

        return ft.View(
            route=f"/lesson/{lesson.id}",
            bgcolor=theme.bg,
            scroll=ft.ScrollMode.AUTO,
            padding=24,
            controls=controls,
        )

    def _card(self, title: str, children: list[ft.Control]) -> ft.Control:
        return ft.Container(
            content=ft.Column(
                [ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=self.theme.text), *children],
                spacing=10,
            ),
            bgcolor=self.theme.card, border_radius=18, padding=20,
        )

    def _build_code_card(self) -> ft.Control:
        theme = self.theme
        lesson = self.lesson

        self.editor = make_code_editor(lesson.starter_code.strip())
        children: list[ft.Control] = [self.editor]

        if lesson.input_prompt:
            self.input_field = ft.TextField(hint_text="Type your answer...", width=240)
            children.append(
                ft.Row(
                    [ft.Text(f"🧑 {lesson.input_prompt}", size=15, color=theme.text), self.input_field],
                    spacing=10,
                )
            )

        self.run_button = ft.Button(
            "▶ RUN", on_click=self._on_run, height=52,
            style=ft.ButtonStyle(bgcolor=theme.success, color="#FFFFFF"),
        )
        self.stop_button = ft.Button(
            "⏹ STOP", on_click=self._on_stop, disabled=True, height=52,
            style=ft.ButtonStyle(bgcolor=theme.danger, color="#FFFFFF"),
        )
        reset_button = ft.Button(
            "↺ Reset", on_click=self._on_reset, height=48,
            style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
        )
        self.hint_button = ft.Button(
            "💡 Hint", on_click=self._on_hint, disabled=not lesson.hints, height=48,
            style=ft.ButtonStyle(bgcolor=theme.warning, color="#FFFFFF"),
        )
        children.append(
            ft.Row([self.run_button, self.stop_button, reset_button, self.hint_button], spacing=10, wrap=True)
        )

        self.hint_text = ft.Text("", size=14, color=theme.warning)
        children.append(self.hint_text)

        return self._card("📝 Your Code", children)

    def _build_output_card(self) -> ft.Control:
        theme = self.theme
        self.output_text = ft.Text("Press RUN to see what happens!", size=15, color=theme.text_muted)
        self.details_button = ft.TextButton(
            "🔍 I'm curious (show technical details)", on_click=self._toggle_details,
            visible=False, style=ft.ButtonStyle(color=theme.text_muted),
        )
        self.details_text = ft.Text("", size=12, font_family="Consolas", color="#F1F1F1", selectable=True)
        self.details_container = ft.Container(
            content=self.details_text, bgcolor="#1E1E2E", border_radius=8, padding=12, visible=False,
        )
        return self._card("💻 What Python Says", [self.output_text, self.details_button, self.details_container])

    def _build_game_panel(self) -> ft.Control:
        self._game_title_text = ft.Text(self.lesson.title, size=16, weight=ft.FontWeight.BOLD, color="#FFFFFF")
        self._game_canvas_control = cv.Canvas(shapes=[])
        self._game_container = ft.Container(
            content=self._game_canvas_control, bgcolor="#2A2A2A", width=360, height=280, border_radius=8,
        )
        return self._card("🎮 Your Game", [self._game_title_text, self._game_container, self._build_dpad()])

    def _build_dpad(self) -> ft.Control:
        theme = self.theme

        def key_button(label: str, key: str, size: int = 56) -> ft.Control:
            return ft.Button(
                label, width=size, height=size,
                on_click=lambda _e, k=key: self._trigger_game_key(k),
                style=ft.ButtonStyle(bgcolor=theme.primary, color="#FFFFFF"),
            )

        cross = ft.Column(
            [
                ft.Row([key_button("⬆", "Up")], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(
                    [key_button("⬅", "Left"), key_button("⬇", "Down"), key_button("➡", "Right")],
                    alignment=ft.MainAxisAlignment.CENTER, spacing=8,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
        )
        space_button = ft.Button(
            "⏺ space", width=90, height=64,
            on_click=lambda _e: self._trigger_game_key("space"),
            style=ft.ButtonStyle(bgcolor=theme.warning, color="#FFFFFF"),
        )
        return ft.Row([cross, space_button], alignment=ft.MainAxisAlignment.CENTER, spacing=30)

    def _trigger_game_key(self, key: str) -> None:
        if self.game_canvas is not None:
            self.game_canvas.trigger_key(key)

    def _on_keyboard_event(self, e: ft.KeyboardEvent) -> None:
        key = _KEY_NAME_MAP.get(e.key)
        if key is not None:
            self._trigger_game_key(key)

    def _build_reward_card(self) -> None:
        theme = self.theme
        self.reward_text = ft.Text("", size=22, weight=ft.FontWeight.BOLD, color=theme.text)
        self.badge_text = ft.Text("", size=16, color=theme.text)
        self.reward_card = ft.Container(
            content=ft.Column(
                [
                    self.reward_text,
                    self.badge_text,
                    ft.Button(
                        "CONTINUE ➜", on_click=self._on_continue, height=56,
                        style=ft.ButtonStyle(bgcolor=theme.primary, color="#FFFFFF"),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10,
            ),
            bgcolor="#FFF3D0", border_radius=18, padding=24, visible=False,
        )

    # -- run flow -----------------------------------------------------------
    async def _on_run(self, e) -> None:
        if self._running:
            return
        if self.lesson.graphical:
            await self._on_run_graphical()
            return

        self._running = True
        self.run_button.disabled = True
        self.stop_button.disabled = False
        self._hide_details()
        self.output_text.value = "⏳ Running your code..."
        self.output_text.color = self.theme.text_muted
        self.page.update()

        code = self.editor.value or ""
        handle = RunHandle()
        self._run_handle = handle

        input_value = self.input_field.value if self.input_field is not None else None
        self._current_input_value = input_value
        stdin_text = f"{input_value}\n" if input_value is not None else None

        result = await asyncio.to_thread(run_code, code, handle=handle, stdin_text=stdin_text)
        self._on_run_complete(result, handle)

    def _on_run_complete(self, result: ExecutionResult, handle: RunHandle) -> None:
        self._running = False
        self.run_button.disabled = False
        self.stop_button.disabled = True

        if result.blocked:
            self._show_output(f"🚫 {result.blocked_message}", self.theme.danger)
            self.state.progress.log_event(self.lesson.id, "attempt_blocked", result.blocked_message)
            self.page.update()
            return

        if result.timed_out:
            if handle.cancelled:
                self._show_output("⏹ Stopped.", self.theme.text_muted)
            else:
                self._show_output(
                    "⏳ Your code is taking too long — maybe there's a loop that never stops?",
                    self.theme.danger,
                )
                self.state.progress.log_event(self.lesson.id, "attempt_timeout")
            self.page.update()
            return

        if not result.success:
            friendly, hint = translate_error(result.stderr)
            line = extract_error_line_number(result.stderr)
            if line:
                friendly = f"{friendly} (near line {line})"
            self._show_output(f"{friendly}\n\n💡 {hint}", self.theme.danger, raw=result.stderr)
            self.state.progress.log_event(self.lesson.id, "attempt_error", result.stderr[-200:])
            self.page.update()
            return

        if validate_output(
            result.stdout, self.lesson.expected_output,
            input_value=self._current_input_value,
            expected_output_pattern=self.lesson.expected_output_pattern,
        ):
            self._show_output(result.stdout or "(no output)", self.theme.success)
            self._on_lesson_success()
        else:
            self._show_output(
                f"Python said:\n{result.stdout or '(no output)'}\n\n"
                "That's not quite what we're looking for yet — give it another try!",
                self.theme.warning,
            )
            self.state.progress.log_event(self.lesson.id, "attempt_wrong_output", result.stdout[-200:])
        self.page.update()

    async def _on_run_graphical(self) -> None:
        if self.game_canvas is not None:
            self.game_canvas.cancel_pending()

        self._game_canvas_control.shapes.clear()
        self._game_title_text.value = self.lesson.title
        self._game_container.bgcolor = "#2A2A2A"
        self.page.update()

        self.game_canvas = GameCanvas(
            self._game_canvas_control, self._game_container, self._game_title_text, self.page,
        )

        self._hide_details()
        code = self.editor.value or ""

        result = run_code(code, game=self.game_canvas, disallow_while=True)

        if result.blocked:
            self._show_output(f"🚫 {result.blocked_message}", self.theme.danger)
            self.state.progress.log_event(self.lesson.id, "attempt_blocked", result.blocked_message)
            self.page.update()
            return

        if not result.success:
            friendly, hint = translate_error(result.stderr)
            line = extract_error_line_number(result.stderr)
            if line:
                friendly = f"{friendly} (near line {line})"
            self._show_output(f"{friendly}\n\n💡 {hint}", self.theme.danger, raw=result.stderr)
            self.state.progress.log_event(self.lesson.id, "attempt_error", result.stderr[-200:])
            self.page.update()
            return

        self._show_output("🎮 Your game is running! Check it out above.", self.theme.success)
        self._on_lesson_success()
        self.page.update()

    def _on_stop(self, e) -> None:
        if self._run_handle is not None:
            self._run_handle.cancel()

    def _on_reset(self, e) -> None:
        self.editor.value = self.lesson.starter_code.strip()
        if self.input_field is not None:
            self.input_field.value = ""
        if self.game_canvas is not None:
            self.game_canvas.cancel_pending()
            self._game_canvas_control.shapes.clear()
        self._hide_details()
        self.output_text.value = "Press RUN to see what happens!"
        self.output_text.color = self.theme.text_muted
        self.reward_card.visible = False
        self.page.update()

    def _on_hint(self, e) -> None:
        if not self.lesson.hints:
            return
        hint = self.lesson.hints[self._hint_index % len(self.lesson.hints)]
        self.hint_text.value = f"💡 {hint}"
        self.state.progress.log_event(self.lesson.id, "hint_used", hint)
        self._hint_index += 1
        self.page.update()

    # -- output helpers -----------------------------------------------------
    def _show_output(self, text: str, color: str, raw: str | None = None) -> None:
        self.output_text.value = text
        self.output_text.color = color
        if raw:
            self.details_button.visible = True
            self.details_text.value = raw
        else:
            self._hide_details()

    def _toggle_details(self, e) -> None:
        self.details_container.visible = not self.details_container.visible
        self.page.update()

    def _hide_details(self) -> None:
        self.details_button.visible = False
        self.details_container.visible = False

    # -- success / reward -----------------------------------------------------
    def _on_lesson_success(self) -> None:
        if self._lesson_passed:
            return
        self._lesson_passed = True

        progress = self.state.progress
        progress.complete_lesson(self.lesson.id, self.lesson.reward_stars)
        badge_newly_awarded = False
        if self.lesson.badge:
            badge_newly_awarded = progress.award_badge(self.lesson.badge)

        next_lesson = self.state.lesson_engine.next_after(self.lesson.id)
        if next_lesson:
            progress.set_current_lesson(next_lesson.id)
            progress.set_level(next_lesson.level)

        self.reward_text.value = (
            f"🎉 Great job! You earned {'⭐' * self.lesson.reward_stars} "
            f"({self.lesson.reward_stars} stars)"
        )
        self.badge_text.value = (
            f"🎖️ New badge unlocked: {self.lesson.badge.replace('_', ' ').title()}!"
            if badge_newly_awarded else ""
        )
        self.reward_card.visible = True

    def _on_continue(self, e) -> None:
        if self.game_canvas is not None:
            self.game_canvas.cancel_pending()
        if self.lesson.graphical:
            self.page.on_keyboard_event = None
        self.page.go("/dashboard")

    def _on_menu(self, e) -> None:
        if self._run_handle is not None:
            self._run_handle.cancel()
        if self.game_canvas is not None:
            self.game_canvas.cancel_pending()
        if self.lesson.graphical:
            self.page.on_keyboard_event = None
        self.page.go("/dashboard")
