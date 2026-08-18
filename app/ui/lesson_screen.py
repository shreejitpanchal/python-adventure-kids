"""The Explain -> Demonstrate -> Try It -> Run -> Result -> Challenge -> Reward lesson flow."""
from __future__ import annotations

import threading

import customtkinter as ctk

from app.audio.player import play_sound_ctk, success_sound_for
from app.engine.categories import COURSE_CATEGORIES, get_category_meta
from app.engine.course_status import next_topic_item
from app.engine.lesson import Lesson
from app.engine.validator import validate_ast_contains, validate_output
from app.games.game_window import GameWindow
from app.games.graphical_runner import run_graphical_code
from app.sandbox.errors import extract_error_line_number, translate_error
from app.sandbox.runner import ExecutionResult, RunHandle, run_code
from app.ui import theme
from app.ui.code_editor import CodeEditor, make_read_only_code_block
from app.ui.color_utils import contrasting_text_color

_REWARD_CARD_COLOR = "#FFF3D0"


class LessonScreen(ctk.CTkFrame):
    def __init__(self, app, lesson_id: str) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app
        self.lesson: Lesson = app.lesson_engine.get(lesson_id)

        self._running = False
        self._run_handle: RunHandle | None = None
        self._hint_index = 0
        self._lesson_passed = False
        self._next_in_category_id: str | None = None
        self._next_mission_id: str | None = None
        self._current_input_value: str | None = None
        self.input_entry: ctk.CTkEntry | None = None
        self.game_window: GameWindow | None = None

        self._build_header()

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        self._build_explanation_card()
        self._build_example_card()
        self._build_challenge_card()
        self._build_code_card()
        self._build_output_card()
        self._build_reward_card()

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
            header, text=self.lesson.title, font=theme.font_title(26),
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
    def _build_explanation_card(self) -> None:
        card = self._card("📖 Let's Learn")
        ctk.CTkLabel(
            card, text=self.lesson.explanation.strip(), font=theme.font_body(16),
            text_color=theme.COLOR_TEXT, justify="left", wraplength=820,
        ).pack(anchor="w", padx=24, pady=(0, 20))

    def _build_example_card(self) -> None:
        card = self._card("👀 Example")
        block = make_read_only_code_block(card, self.lesson.example_code.strip(), height=60)
        block.pack(fill="x", padx=24, pady=(0, 20))

    def _build_challenge_card(self) -> None:
        card = self._card("🎯 Try It")
        ctk.CTkLabel(
            card, text=self.lesson.challenge.strip(), font=theme.font_body(15),
            text_color=theme.COLOR_TEXT_MUTED, justify="left", wraplength=820,
        ).pack(anchor="w", padx=24, pady=(0, 20))

    def _build_code_card(self) -> None:
        card = self._card("📝 Your Code")

        self.editor = CodeEditor(card, height=140)
        self.editor.pack(fill="x", padx=24, pady=(0, 12))
        self.editor.set_code(self.lesson.starter_code.strip())

        if self.lesson.input_prompt:
            input_row = ctk.CTkFrame(card, fg_color="transparent")
            input_row.pack(fill="x", padx=24, pady=(0, 12))
            # Stacked (label above, box below), not side-by-side -- at
            # larger font sizes the label alone can grow wider than the
            # card, which pushed the fixed-width entry box off-screen when
            # both shared one row.
            ctk.CTkLabel(
                input_row, text=f"🧑 {self.lesson.input_prompt}", font=theme.font_body(15),
                text_color=theme.COLOR_TEXT, anchor="w", justify="left", wraplength=760,
            ).pack(anchor="w", pady=(0, 6))
            self.input_entry = ctk.CTkEntry(
                input_row, font=theme.font_body(16), width=240, height=40,
                placeholder_text="Type your answer...",
            )
            self.input_entry.pack(anchor="w")

        button_row = ctk.CTkFrame(card, fg_color="transparent")
        button_row.pack(fill="x", padx=24, pady=(0, 12))

        self.run_button = ctk.CTkButton(
            button_row, text="▶ RUN", font=theme.font_button(18), width=140, height=48,
            fg_color=theme.COLOR_SUCCESS, hover_color=theme.COLOR_SUCCESS_HOVER,
            command=self._on_run,
        )
        self.run_button.pack(side="left", padx=(0, 10))

        self.stop_button = ctk.CTkButton(
            button_row, text="⏹ STOP", font=theme.font_button(16), width=110, height=48,
            fg_color=theme.COLOR_DANGER, hover_color="#D94F4F",
            command=self._on_stop, state="disabled",
        )
        self.stop_button.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            button_row, text="↺ Reset", font=theme.font_body(15), width=110, height=48,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._on_reset,
        ).pack(side="left", padx=(0, 10))

        self.hint_button = ctk.CTkButton(
            button_row, text="💡 Hint", font=theme.font_body(15), width=110, height=48,
            fg_color=theme.COLOR_WARNING, hover_color="#E09A1F",
            command=self._on_hint,
        )
        self.hint_button.pack(side="left")
        if not self.lesson.hints:
            self.hint_button.configure(state="disabled")

        self.hint_label = ctk.CTkLabel(
            card, text="", font=theme.font_body(14), text_color=theme.COLOR_WARNING,
            justify="left", wraplength=820,
        )
        self.hint_label.pack(anchor="w", padx=24, pady=(0, 18))

    def _build_output_card(self) -> None:
        card = self._card("💻 What Python Says")

        self.output_label = ctk.CTkLabel(
            card, text="Press RUN to see what happens!", font=theme.font_body(16),
            text_color=theme.COLOR_TEXT_MUTED, justify="left", wraplength=820,
        )
        self.output_label.pack(anchor="w", padx=24, pady=(0, 8))

        self.details_button = ctk.CTkButton(
            card, text="🔍 I'm curious (show technical details)", font=theme.font_body(12),
            fg_color="transparent", text_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_BG,
            width=280, height=28, command=self._toggle_details,
        )
        self.details_button.pack(anchor="w", padx=20)
        self.details_button.pack_forget()

        self.details_box = ctk.CTkTextbox(
            card, height=100, font=theme.font_mono(12),
            fg_color="#1E1E2E", text_color="#F1F1F1",
        )
        self._details_visible = False

    def _build_reward_card(self) -> None:
        # The reward card's cream background is fixed regardless of the
        # active theme (a deliberate always-celebratory look), so its text
        # must be too -- theme.COLOR_TEXT is tuned for dark themes' own
        # dark background and turns near-invisible on this light card (#2547).
        reward_text_color = contrasting_text_color(_REWARD_CARD_COLOR)
        self.reward_card = ctk.CTkFrame(self.body, fg_color=_REWARD_CARD_COLOR, corner_radius=18)

        self.reward_label = ctk.CTkLabel(
            self.reward_card, text="", font=theme.font_title(24),
            text_color=reward_text_color, justify="center",
        )
        self.reward_label.pack(pady=(24, 6))

        self.badge_label = ctk.CTkLabel(
            self.reward_card, text="", font=theme.font_heading(16),
            text_color=reward_text_color,
        )
        self.badge_label.pack(pady=(0, 10))

        # Course lessons keep the original Onward/Next Lesson pair (chapter
        # navigation, not a "mission") -- only Today's Mission lessons
        # (outside COURSE_CATEGORIES) get the Next Mission/Next Level
        # framing below, since only those participate in next_after()'s
        # round-robin at all.
        if self.lesson.category in COURSE_CATEGORIES:
            self.next_mission_caption = None
            self.next_lesson_caption = None

            button_row = ctk.CTkFrame(self.reward_card, fg_color="transparent")
            button_row.pack(pady=(0, 24))

            ctk.CTkButton(
                button_row, text="ONWARD ➜", font=theme.font_button(20), width=200, height=56,
                fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
                command=self._on_continue,
            ).pack(side="left", padx=6)

            self.next_lesson_button = ctk.CTkButton(
                button_row, text="NEXT LESSON ➜", font=theme.font_button(20), width=200, height=56,
                fg_color=theme.COLOR_SUCCESS, hover_color=theme.COLOR_SUCCESS_HOVER,
                command=self._on_next_lesson,
            )
            self._next_lesson_button_pack_kwargs = {"side": "left", "padx": 6}
            self.next_lesson_button.pack(**self._next_lesson_button_pack_kwargs)
        else:
            button_column = ctk.CTkFrame(self.reward_card, fg_color="transparent")
            button_column.pack(pady=(0, 24))

            ctk.CTkButton(
                button_column, text="Next Mission ➜", font=theme.font_button(20), width=280, height=56,
                fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
                command=self._on_continue,
            ).pack()
            self.next_mission_caption = ctk.CTkLabel(
                button_column, text="", font=theme.font_italic(13), text_color=reward_text_color,
            )
            self.next_mission_caption.pack(pady=(2, 12))

            self.next_lesson_button = ctk.CTkButton(
                button_column, text="Next Level ➜", font=theme.font_button(20), width=280, height=56,
                fg_color=theme.COLOR_SUCCESS, hover_color=theme.COLOR_SUCCESS_HOVER,
                command=self._on_next_lesson,
            )
            self._next_lesson_button_pack_kwargs = {"pady": (2, 0)}
            self.next_lesson_button.pack()
            self.next_lesson_caption = ctk.CTkLabel(
                button_column, text="", font=theme.font_italic(13), text_color=reward_text_color,
            )
            self.next_lesson_caption.pack(pady=(2, 0))

    # -- run flow -------------------------------------------------------------
    def _on_run(self) -> None:
        if self._running:
            return
        if self.lesson.graphical:
            self._on_run_graphical()
            return

        self._running = True
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.editor.clear_error_highlight()
        self._hide_details()
        self.output_label.configure(text="⏳ Running your code...", text_color=theme.COLOR_TEXT_MUTED)

        code = self.editor.get_code()
        handle = RunHandle()
        self._run_handle = handle

        input_value = self.input_entry.get() if self.input_entry is not None else None
        self._current_input_value = input_value
        stdin_text = f"{input_value}\n" if input_value is not None else None

        thread = threading.Thread(
            target=self._execute_in_background, args=(code, handle, stdin_text), daemon=True,
        )
        thread.start()

    def _execute_in_background(self, code: str, handle: RunHandle, stdin_text: str | None) -> None:
        result = run_code(code, handle=handle, stdin_text=stdin_text)
        self.app.after(0, lambda: self._on_run_complete(result, handle))

    def _on_run_complete(self, result: ExecutionResult, handle: RunHandle) -> None:
        self._running = False
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

        if result.blocked:
            self._show_output(f"🚫 {result.blocked_message}", theme.COLOR_DANGER)
            self.app.progress.log_event(self.lesson.id, "attempt_blocked", result.blocked_message)
            return

        if result.timed_out:
            if handle.cancelled:
                self._show_output("⏹ Stopped.", theme.COLOR_TEXT_MUTED)
            else:
                self._show_output(
                    "⏳ Your code is taking too long — maybe there's a loop that never stops?",
                    theme.COLOR_DANGER,
                )
                self.app.progress.log_event(self.lesson.id, "attempt_timeout")
            return

        if not result.success:
            friendly, hint = translate_error(result.stderr)
            self._show_output(f"{friendly}\n\n💡 {hint}", theme.COLOR_DANGER, raw=result.stderr)
            line = extract_error_line_number(result.stderr)
            if line:
                self.editor.highlight_error_line(line)
            self.app.progress.log_event(self.lesson.id, "attempt_error", result.stderr[-200:])
            return

        output_ok = validate_output(
            result.stdout, self.lesson.expected_output,
            input_value=self._current_input_value,
            expected_output_pattern=self.lesson.expected_output_pattern,
        )
        ast_ok = (
            validate_ast_contains(self.editor.get_code(), self.lesson.ast_contains)
            if self.lesson.ast_contains else True
        )

        if output_ok and ast_ok:
            self._show_output(result.stdout or "(no output)", theme.COLOR_SUCCESS)
            self._on_lesson_success()
        elif output_ok and not ast_ok:
            self._show_output(
                f"Python said:\n{result.stdout or '(no output)'}\n\n"
                "That's the right answer, but try solving it using what this lesson "
                "is teaching, not just typing the answer directly!",
                theme.COLOR_WARNING,
            )
        else:
            self._show_output(
                f"Python said:\n{result.stdout or '(no output)'}\n\n"
                "That's not quite what we're looking for yet — give it another try!",
                theme.COLOR_WARNING,
            )
            self.app.progress.log_event(self.lesson.id, "attempt_wrong_output", result.stdout[-200:])

    # -- graphical run flow (Snake-style lessons) ------------------------------
    def _on_run_graphical(self) -> None:
        self.editor.clear_error_highlight()
        self._hide_details()
        self._close_game_window()

        self.game_window = GameWindow(self.app, on_close=self._forget_game_window)
        code = self.editor.get_code()
        result = run_graphical_code(code, self.game_window.game_canvas)

        if result.blocked:
            self._show_output(f"🚫 {result.blocked_message}", theme.COLOR_DANGER)
            self.app.progress.log_event(self.lesson.id, "attempt_blocked", result.blocked_message)
            return

        if not result.success:
            friendly, hint = translate_error(result.traceback_text)
            self._show_output(f"{friendly}\n\n💡 {hint}", theme.COLOR_DANGER, raw=result.traceback_text)
            line = extract_error_line_number(result.traceback_text)
            if line:
                self.editor.highlight_error_line(line)
            self.app.progress.log_event(self.lesson.id, "attempt_error", result.traceback_text[-200:])
            return

        ast_ok = (
            validate_ast_contains(code, self.lesson.ast_contains) if self.lesson.ast_contains else True
        )
        if not ast_ok:
            self._show_output(
                "🎮 Your game ran, but try solving it using what this lesson is teaching!",
                theme.COLOR_WARNING,
            )
            return

        self._show_output("🎮 Your game is running! Check out the window that just opened.", theme.COLOR_SUCCESS)
        self._on_lesson_success()

    def _forget_game_window(self) -> None:
        self.game_window = None

    def _close_game_window(self) -> None:
        if self.game_window is not None:
            self.game_window.close()
            self.game_window = None

    def _on_stop(self) -> None:
        if self._run_handle is not None:
            self._run_handle.cancel()

    def _on_reset(self) -> None:
        self.editor.set_code(self.lesson.starter_code.strip())
        self.editor.clear_error_highlight()
        if self.input_entry is not None:
            self.input_entry.delete(0, "end")
        self._hide_details()
        self._close_game_window()
        self.output_label.configure(
            text="Press RUN to see what happens!", text_color=theme.COLOR_TEXT_MUTED,
        )
        self.reward_card.pack_forget()

    def _on_hint(self) -> None:
        if not self.lesson.hints:
            return
        hint = self.lesson.hints[self._hint_index % len(self.lesson.hints)]
        self.hint_label.configure(text=f"💡 {hint}")
        self.app.progress.log_event(self.lesson.id, "hint_used", hint)
        self._hint_index += 1

    # -- output helpers -----------------------------------------------------
    def _show_output(self, text: str, color: str, raw: str | None = None) -> None:
        self.output_label.configure(text=text, text_color=color)
        if raw:
            self.details_button.pack(anchor="w", padx=20)
            self.details_box.configure(state="normal")
            self.details_box.delete("1.0", "end")
            self.details_box.insert("1.0", raw)
            self.details_box.configure(state="disabled")
        else:
            self._hide_details()

    def _toggle_details(self) -> None:
        self._details_visible = not self._details_visible
        if self._details_visible:
            self.details_box.pack(fill="x", padx=24, pady=(0, 20))
        else:
            self.details_box.pack_forget()

    def _hide_details(self) -> None:
        self.details_button.pack_forget()
        self.details_box.pack_forget()
        self._details_visible = False

    # -- success / reward -----------------------------------------------------
    def _on_lesson_success(self) -> None:
        if self._lesson_passed:
            return
        self._lesson_passed = True

        progress = self.app.progress
        level_before = progress.get_player_level().level
        progress.complete_lesson(self.lesson.id, self.lesson.reward_stars)
        badge_newly_awarded = False
        if self.lesson.badge:
            badge_newly_awarded = progress.award_badge(self.lesson.badge)
        leveled_up = progress.get_player_level().level > level_before

        for sound_name in success_sound_for(leveled_up=leveled_up, badge_earned=badge_newly_awarded):
            play_sound_ctk(sound_name, self.app.settings)

        next_lesson = self.app.lesson_engine.next_after(self.lesson.id)
        if next_lesson:
            progress.set_current_lesson(next_lesson.id)
            progress.set_level(next_lesson.level)
        self._next_mission_id = next_lesson.id if next_lesson else None

        self.reward_label.configure(
            text=f"🎉 Great job! You earned {'⭐' * self.lesson.reward_stars} "
                 f"({self.lesson.reward_stars} stars)"
        )
        self.badge_label.configure(
            text=f"🎖️ New badge unlocked: {self.lesson.badge.replace('_', ' ').title()}!"
            if badge_newly_awarded else ""
        )

        completed_ids = progress.get_completed_lesson_ids()
        if self.lesson.category in COURSE_CATEGORIES:
            next_in_category = next_topic_item(self.app.lesson_engine, self.lesson, completed_ids)
        else:
            next_in_category = self.app.lesson_engine.next_unlocked_in_category(
                self.lesson.category, completed_ids,
            )
        self._next_in_category_id = next_in_category.id if next_in_category else None
        if next_in_category is not None:
            self.next_lesson_button.pack(**self._next_lesson_button_pack_kwargs)
        else:
            self.next_lesson_button.pack_forget()

        if self.next_mission_caption is not None:
            if next_lesson:
                meta = get_category_meta(next_lesson.category)
                self.next_mission_caption.configure(text=f"{meta.icon} {meta.title} — Level {next_lesson.category_level}")
            else:
                self.next_mission_caption.configure(text="You've completed Today's Mission! 🎉")
        if self.next_lesson_caption is not None:
            if next_in_category:
                meta = get_category_meta(next_in_category.category)
                self.next_lesson_caption.configure(text=f"{meta.icon} {meta.title} — Level {next_in_category.category_level}")
            else:
                self.next_lesson_caption.configure(text="")

        self.reward_card.pack(fill="x", pady=10)

    def _on_continue(self) -> None:
        if self.lesson.category in COURSE_CATEGORIES:
            self.app.show_course_chapter(self.lesson.category)
        elif self._next_mission_id:
            self.app.show_lesson_or_quiz(self._next_mission_id)
        else:
            self.app.show_dashboard()

    def _on_next_lesson(self) -> None:
        if self._next_in_category_id:
            self.app.show_lesson_or_quiz(self._next_in_category_id)

    def _on_menu(self) -> None:
        if self._run_handle is not None:
            self._run_handle.cancel()
        self._close_game_window()
        self.app.show_hub()
