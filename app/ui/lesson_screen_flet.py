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

from app.audio.player import success_sound_for
from app.engine.badges import get_badge_meta
from app.engine.lesson import Lesson
from app.engine.validator import validate_ast_contains, validate_output
from app.games.game_canvas_flet import GameCanvas
from app.sandbox.errors import extract_error_line_number, translate_error
from app.sandbox.inprocess_runner import ExecutionResult, RunHandle, run_code
from app.ui.app_state_flet import AppState
from app.ui.code_editor_flet import make_code_editor, make_read_only_code_block
from app.ui.components.codey_avatar_flet import CodeyState, build_codey_avatar
from app.ui.components.macro_toolbar_flet import build_macro_toolbar
from app.ui.components.victory_overlay_flet import build_victory_overlay

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
        self._build_victory_overlay()

        controls = [header, explanation_card, example_card, challenge_card, code_card]
        if game_panel is not None:
            controls.append(
                ft.KeyboardListener(
                    content=game_panel, autofocus=True,
                    on_key_down=self._on_key_down, on_key_up=self._on_key_up,
                )
            )
        controls.append(output_card)

        # The victory overlay is a full-screen Stack layer, not another item
        # in the scrolling column -- see app/ui/components/victory_overlay_flet.py.
        content = ft.Container(
            content=ft.Column(controls, scroll=ft.ScrollMode.AUTO, spacing=10, expand=True),
            padding=24, expand=True,
        )

        return ft.View(
            route=f"/lesson/{lesson.id}",
            bgcolor=theme.bg,
            padding=0,
            controls=[ft.Stack([content, self.reward_card], expand=True)],
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

        self._codey = build_codey_avatar(theme)

        self.editor = make_code_editor(lesson.starter_code.strip())
        self.macro_toolbar = build_macro_toolbar(self.editor, self.page, theme)
        children: list[ft.Control] = [self._codey.control, self.editor, self.macro_toolbar]

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
        self.practice_quest_row = ft.Row([], spacing=8, wrap=True)
        self.practice_quest_container = ft.Container(
            content=ft.Column(
                [
                    ft.Text("💡 Practice Quest: stuck? These might help!", size=14, weight=ft.FontWeight.BOLD, color=theme.text),
                    self.practice_quest_row,
                    ft.TextButton("✕ Dismiss", on_click=self._dismiss_practice_quest, style=ft.ButtonStyle(color=theme.text_muted)),
                ],
                spacing=8,
            ),
            bgcolor=theme.card, border=ft.border.Border.all(2, theme.warning), border_radius=8, padding=12,
            visible=False,
        )
        return self._card(
            "💻 What Python Says",
            [self.output_text, self.details_button, self.details_container, self.practice_quest_container],
        )

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

    def _on_key_down(self, e: ft.KeyDownEvent) -> None:
        key = _KEY_NAME_MAP.get(e.key)
        if key is None:
            return
        self._trigger_game_key(key)
        if self.game_canvas is not None:
            self.game_canvas.key_down(key)

    def _on_key_up(self, e: ft.KeyUpEvent) -> None:
        key = _KEY_NAME_MAP.get(e.key)
        if key is not None and self.game_canvas is not None:
            self.game_canvas.key_up(key)

    def _build_victory_overlay(self) -> None:
        # self.reward_card is kept as the name for the overlay's root Stack
        # control (it's still just an ft.Control with a .visible flag) so
        # the rest of this class -- and every existing test -- didn't need
        # to change to know about the new presentation.
        handle = build_victory_overlay(self.page, self.theme, self._on_continue)
        self._victory_handle = handle
        self.reward_card = handle.overlay
        self.reward_text = handle.reward_text
        self.badge_text = handle.badge_text

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
        self._codey.set_state(CodeyState.RUNNING)
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
            self._codey.set_state(CodeyState.BLOCKED)
            self.state.progress.log_event(self.lesson.id, "attempt_blocked", result.blocked_message)
            self.page.update()
            return

        if result.timed_out:
            if handle.cancelled:
                self._show_output("⏹ Stopped.", self.theme.text_muted)
                self._codey.set_state(CodeyState.IDLE)
            else:
                self._show_output(
                    "⏳ Your code is taking too long — maybe there's a loop that never stops?",
                    self.theme.danger,
                )
                self._codey.set_state(CodeyState.WARNING)
                self.state.progress.log_event(self.lesson.id, "attempt_timeout")
                self._maybe_show_practice_quest()
            self.page.update()
            return

        if not result.success:
            friendly, hint = translate_error(result.stderr)
            line = extract_error_line_number(result.stderr)
            if line:
                friendly = f"{friendly} (near line {line})"
            self._show_output(f"{friendly}\n\n💡 {hint}", self.theme.danger, raw=result.stderr)
            self._codey.set_state(CodeyState.ERROR)
            self.state.progress.log_event(self.lesson.id, "attempt_error", result.stderr[-200:])
            self._maybe_show_practice_quest()
            self.page.update()
            return

        output_ok = validate_output(
            result.stdout, self.lesson.expected_output,
            input_value=self._current_input_value,
            expected_output_pattern=self.lesson.expected_output_pattern,
        )
        ast_ok = (
            validate_ast_contains(self.editor.value or "", self.lesson.ast_contains)
            if self.lesson.ast_contains else True
        )

        if output_ok and ast_ok:
            self._hide_practice_quest()
            self._show_output(result.stdout or "(no output)", self.theme.success)
            self._codey.set_state(CodeyState.SUCCESS)
            self._on_lesson_success()
        elif output_ok and not ast_ok:
            self._show_output(
                f"Python said:\n{result.stdout or '(no output)'}\n\n"
                "That's the right answer, but try solving it using what this lesson "
                "is teaching, not just typing the answer directly!",
                self.theme.warning,
            )
            self._codey.set_state(CodeyState.WARNING)
        else:
            self._show_output(
                f"Python said:\n{result.stdout or '(no output)'}\n\n"
                "That's not quite what we're looking for yet — give it another try!",
                self.theme.warning,
            )
            self._codey.set_state(CodeyState.WARNING)
            self.state.progress.log_event(self.lesson.id, "attempt_wrong_output", result.stdout[-200:])
            self._maybe_show_practice_quest()
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
        self._codey.set_state(CodeyState.RUNNING)
        code = self.editor.value or ""

        result = run_code(code, game=self.game_canvas, disallow_while=True)

        if result.blocked:
            self._show_output(f"🚫 {result.blocked_message}", self.theme.danger)
            self._codey.set_state(CodeyState.BLOCKED)
            self.state.progress.log_event(self.lesson.id, "attempt_blocked", result.blocked_message)
            self.page.update()
            return

        if not result.success:
            friendly, hint = translate_error(result.stderr)
            line = extract_error_line_number(result.stderr)
            if line:
                friendly = f"{friendly} (near line {line})"
            self._show_output(f"{friendly}\n\n💡 {hint}", self.theme.danger, raw=result.stderr)
            self._codey.set_state(CodeyState.ERROR)
            self.state.progress.log_event(self.lesson.id, "attempt_error", result.stderr[-200:])
            self.page.update()
            return

        ast_ok = (
            validate_ast_contains(code, self.lesson.ast_contains) if self.lesson.ast_contains else True
        )
        if not ast_ok:
            self._show_output(
                "🎮 Your game ran, but try solving it using what this lesson is teaching!",
                self.theme.warning,
            )
            self._codey.set_state(CodeyState.WARNING)
            self.page.update()
            return

        mission_ok = True
        if self.lesson.requires_goal_reached:
            mission_ok = bool(getattr(self.game_canvas, "robot_at_goal", lambda: True)())
        if not mission_ok:
            self._show_output(
                "🤖 Your code ran, but the robot didn't reach the goal yet — try again!",
                self.theme.warning,
            )
            self._codey.set_state(CodeyState.WARNING)
            self.page.update()
            return

        self._show_output("🎮 Your game is running! Check it out above.", self.theme.success)
        self._codey.set_state(CodeyState.SUCCESS)
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
        self._hide_practice_quest()
        self.output_text.value = "Press RUN to see what happens!"
        self.output_text.color = self.theme.text_muted
        self._codey.set_state(CodeyState.IDLE)
        self._victory_handle.hide()
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

    # -- adaptive practice ("Practice Quest") --------------------------------
    _PRACTICE_QUEST_THRESHOLD = 3

    def _maybe_show_practice_quest(self) -> None:
        """After enough consecutive failed attempts on this lesson (see
        ProgressStore.get_recent_failure_count()), suggest 1-3 lessons
        sharing a concept_tags entry -- purely additive, never blocks
        retry/hints/continue, and does nothing if the lesson has no
        concept_tags or no failure count has crossed the threshold yet."""
        failures = self.state.progress.get_recent_failure_count(self.lesson.id)
        if failures < self._PRACTICE_QUEST_THRESHOLD:
            return
        completed_ids = self.state.progress.get_completed_lesson_ids()
        suggestions = self.state.lesson_engine.recommend_practice(self.lesson.id, completed_ids)
        if not suggestions:
            return

        self.practice_quest_row.controls = [
            ft.Button(
                lesson.title, height=40,
                on_click=lambda _e, lesson_id=lesson.id: self.page.go(f"/lesson/{lesson_id}"),
                style=ft.ButtonStyle(bgcolor=self.theme.warning, color="#FFFFFF"),
            )
            for lesson in suggestions
        ]
        self.practice_quest_container.visible = True

    def _dismiss_practice_quest(self, e) -> None:
        self._hide_practice_quest()
        self.page.update()

    def _hide_practice_quest(self) -> None:
        self.practice_quest_container.visible = False

    # -- success / reward -----------------------------------------------------
    def _on_lesson_success(self) -> None:
        if self._lesson_passed:
            return
        self._lesson_passed = True

        progress = self.state.progress
        level_before = progress.get_player_level().level
        progress.complete_lesson(self.lesson.id, self.lesson.reward_stars)
        badge_newly_awarded = False
        if self.lesson.badge:
            badge_newly_awarded = progress.award_badge(self.lesson.badge)
        leveled_up = progress.get_player_level().level > level_before

        module_badge_lines = self._award_module_badges()

        if self.state.sound_player is not None:
            badge_earned = badge_newly_awarded or bool(module_badge_lines)
            for sound_name in success_sound_for(leveled_up=leveled_up, badge_earned=badge_earned):
                self.state.sound_player.play(sound_name, self.state.settings)

        next_lesson = self.state.lesson_engine.next_after(self.lesson.id)
        if next_lesson:
            progress.set_current_lesson(next_lesson.id)
            progress.set_level(next_lesson.level)

        self.reward_text.value = (
            f"🎉 Great job! You earned {'⭐' * self.lesson.reward_stars} "
            f"({self.lesson.reward_stars} stars)"
        )
        lesson_badge_line = (
            f"🎖️ New badge unlocked: {self.lesson.badge.replace('_', ' ').title()}!"
            if badge_newly_awarded else ""
        )
        self.badge_text.value = "\n".join(line for line in [lesson_badge_line, *module_badge_lines] if line)
        self._victory_handle.show()

    def _award_module_badges(self) -> list[str]:
        """Awards any Python Journey module badge (and the capstone
        "Python Journey Complete" badge) that this lesson completion just
        satisfied. Also doubles as the migration-free "catch up" check --
        see app/engine/learning_path.py's newly_earned_module_badges() --
        though it only actually runs here on a fresh completion, not on
        every Journey screen load like journey_map_flet.py's version.
        Returns the reward-card lines to show, if any."""
        progress = self.state.progress
        learning_path = self.state.learning_path_engine
        completed_ids = progress.get_completed_lesson_ids()
        already_awarded = progress.get_badge_ids()

        lines: list[str] = []
        for badge_id in learning_path.newly_earned_module_badges(completed_ids, already_awarded):
            progress.award_badge(badge_id)
            lines.append(f"🎖️ Module badge unlocked: {get_badge_meta(badge_id).title}!")

        if "python_journey_complete" not in already_awarded and learning_path.all_modules_complete(completed_ids):
            progress.award_badge("python_journey_complete")
            lines.append(f"🌟 {get_badge_meta('python_journey_complete').title}!")

        return lines

    def _on_continue(self, e) -> None:
        if self.game_canvas is not None:
            self.game_canvas.cancel_pending()
        self.page.go("/dashboard")

    def _on_menu(self, e) -> None:
        if self._run_handle is not None:
            self._run_handle.cancel()
        if self.game_canvas is not None:
            self.game_canvas.cancel_pending()
        self.page.go("/dashboard")
