"""First-run setup wizard: just the child's name and, optionally, a
preferred learning mode -- see app/parent/dashboard.py for Parent Area."""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.ui import theme
from app.ui.assets import make_ctk_icon


class SetupWizardFrame(ctk.CTkFrame):
    def __init__(self, app, on_complete: Callable[[], None]) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app
        self.on_complete = on_complete

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=60, pady=60)

        self._show_welcome_step()

    def _clear_body(self) -> None:
        for child in self._body.winfo_children():
            child.destroy()

    # -- Step 1: child's name -------------------------------------------------
    def _show_welcome_step(self) -> None:
        self._clear_body()

        # Kept as an attribute so the underlying image isn't garbage-collected.
        self.welcome_icon_image = make_ctk_icon(size=44)
        ctk.CTkLabel(
            self._body, text=" Welcome to Python Adventure!", image=self.welcome_icon_image,
            compound="left", font=theme.font_title(), text_color=theme.COLOR_PRIMARY,
        ).pack(pady=(40, 10))

        ctk.CTkLabel(
            self._body, text="What's your name, explorer?", font=theme.font_heading(),
            text_color=theme.COLOR_TEXT,
        ).pack(pady=(30, 20))

        name_entry = ctk.CTkEntry(
            self._body, font=theme.font_body(20), width=320, height=48,
            placeholder_text="Type your name here",
            justify="center",
        )
        name_entry.pack(pady=10)
        name_entry.focus_set()

        error_label = ctk.CTkLabel(self._body, text="", font=theme.font_body(14), text_color=theme.COLOR_DANGER)
        error_label.pack(pady=(0, 10))

        def go_next() -> None:
            name = name_entry.get().strip()
            if not name:
                error_label.configure(text="Please type your name first! 😊")
                return
            self.app.settings.child_name = name
            self._show_mode_step()

        name_entry.bind("<Return>", lambda _e: go_next())

        ctk.CTkButton(
            self._body, text="NEXT ➜", font=theme.font_button(), width=200, height=56,
            fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
            command=go_next,
        ).pack(pady=30)

    # -- Step 2: preferred learning mode (skippable) -----------------------------
    _MODE_OPTIONS = [
        ("guided", "🚀 Learn Python from the beginning"),
        ("projects", "🛠️ Make games and creative projects"),
        ("crackers", "🐛 Practise coding puzzles"),
        ("advanced", "🧠 I already know some Python"),
    ]

    def _show_mode_step(self) -> None:
        self._clear_body()

        ctk.CTkLabel(
            self._body, text="What sounds most fun today?", font=theme.font_title(28),
            text_color=theme.COLOR_PRIMARY,
        ).pack(pady=(40, 10))

        ctk.CTkLabel(
            self._body, text="Pick whatever you're most excited about — you can always try\neverything else from the Learning Hub later.",
            font=theme.font_body(14), text_color=theme.COLOR_TEXT_MUTED, justify="center",
        ).pack(pady=(0, 30))

        card = ctk.CTkFrame(self._body, fg_color=theme.COLOR_CARD, corner_radius=20)
        card.pack(fill="x", padx=40, pady=(0, 20))

        for index, (mode_key, label) in enumerate(self._MODE_OPTIONS):
            top_pad = 20 if index == 0 else 0
            ctk.CTkButton(
                card, text=label, font=theme.font_heading(16), height=52, corner_radius=14,
                fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
                command=lambda key=mode_key: self._on_select_mode(key),
            ).pack(fill="x", padx=20, pady=(top_pad, 10))

        ctk.CTkButton(
            self._body, text="Skip for now", font=theme.font_body(14), width=200, height=40,
            fg_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_TEXT,
            command=self._on_skip_mode,
        ).pack(pady=(0, 20))

    def _on_select_mode(self, mode_key: str) -> None:
        self.app.settings.preferred_learning_mode = mode_key
        self._show_finish_step()

    def _on_skip_mode(self) -> None:
        self.app.settings.preferred_learning_mode = ""
        self._show_finish_step()

    # -- Step 3: finish ----------------------------------------------------------
    def _show_finish_step(self) -> None:
        self._clear_body()

        name = self.app.settings.child_name or "Explorer"

        ctk.CTkLabel(
            self._body, text="🎉", font=theme.font_title(60),
        ).pack(pady=(40, 0))

        ctk.CTkLabel(
            self._body, text=f"All set, {name}!", font=theme.font_title(),
            text_color=theme.COLOR_PRIMARY,
        ).pack(pady=(10, 10))

        ctk.CTkLabel(
            self._body, text="Your Python Adventure is ready to begin.",
            font=theme.font_heading(18), text_color=theme.COLOR_TEXT,
        ).pack(pady=(0, 40))

        def finish() -> None:
            self.app.settings.setup_complete = True
            self.app.save_settings()
            self.on_complete()

        ctk.CTkButton(
            self._body, text="▶ START ADVENTURE", font=theme.font_button(24), width=320, height=64,
            fg_color=theme.COLOR_SUCCESS, hover_color=theme.COLOR_SUCCESS_HOVER,
            command=finish,
        ).pack(pady=10)
