"""First-run setup wizard: child's name and a parent PIN. No technical setup shown to the child."""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.ui import theme


class SetupWizardFrame(ctk.CTkFrame):
    def __init__(self, app, on_complete: Callable[[], None]) -> None:
        super().__init__(app, fg_color=theme.COLOR_BG)
        self.app = app
        self.on_complete = on_complete
        self._pin_first_entry: str | None = None

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=60, pady=60)

        self._show_welcome_step()

    def _clear_body(self) -> None:
        for child in self._body.winfo_children():
            child.destroy()

    # -- Step 1: child's name -------------------------------------------------
    def _show_welcome_step(self) -> None:
        self._clear_body()

        ctk.CTkLabel(
            self._body, text="🐍 Welcome to Python Adventure!", font=theme.font_title(),
            text_color=theme.COLOR_PRIMARY,
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
            self._show_parent_pin_step()

        name_entry.bind("<Return>", lambda _e: go_next())

        ctk.CTkButton(
            self._body, text="NEXT ➜", font=theme.font_button(), width=200, height=56,
            fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
            command=go_next,
        ).pack(pady=30)

    # -- Step 2: parent PIN ----------------------------------------------------
    def _show_parent_pin_step(self) -> None:
        self._clear_body()
        self._pin_first_entry = None

        ctk.CTkLabel(
            self._body, text="👋 Grown-ups only", font=theme.font_title(28),
            text_color=theme.COLOR_PRIMARY,
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            self._body,
            text="Set a 4-digit PIN to unlock the Parent Area later.",
            font=theme.font_body(16),
            text_color=theme.COLOR_TEXT_MUTED,
        ).pack(pady=(0, 30))

        pin_entry = ctk.CTkEntry(
            self._body, font=theme.font_body(24), width=200, height=48,
            placeholder_text="••••", justify="center", show="•",
        )
        pin_entry.pack(pady=10)
        pin_entry.focus_set()

        error_label = ctk.CTkLabel(self._body, text="", font=theme.font_body(14), text_color=theme.COLOR_DANGER)
        error_label.pack(pady=(0, 10))

        def submit_pin() -> None:
            pin = pin_entry.get().strip()
            if not (pin.isdigit() and len(pin) == 4):
                error_label.configure(text="Please enter exactly 4 digits.")
                return
            if self._pin_first_entry is None:
                self._pin_first_entry = pin
                pin_entry.delete(0, "end")
                error_label.configure(text_color=theme.COLOR_SUCCESS, text="Type it again to confirm.")
                return
            if pin != self._pin_first_entry:
                self._pin_first_entry = None
                pin_entry.delete(0, "end")
                error_label.configure(text_color=theme.COLOR_DANGER, text="PINs didn't match. Try again.")
                return
            self.app.settings.set_parent_pin(pin)
            self._show_finish_step()

        pin_entry.bind("<Return>", lambda _e: submit_pin())

        ctk.CTkButton(
            self._body, text="NEXT ➜", font=theme.font_button(), width=200, height=56,
            fg_color=theme.COLOR_PRIMARY, hover_color=theme.COLOR_PRIMARY_HOVER,
            command=submit_pin,
        ).pack(pady=20)

        ctk.CTkButton(
            self._body, text="Skip for now", font=theme.font_body(14), width=160, height=32,
            fg_color="transparent", text_color=theme.COLOR_TEXT_MUTED, hover_color=theme.COLOR_BG,
            command=self._show_finish_step,
        ).pack()

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
