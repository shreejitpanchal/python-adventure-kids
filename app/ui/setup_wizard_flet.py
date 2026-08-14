"""First-run setup wizard: child's name and a parent PIN. No technical setup shown to the child."""
from __future__ import annotations

import flet as ft

from app.ui.app_state_flet import AppState
from app.ui.theme_flet import ThemePreset


def build_setup_wizard_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    body = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    wizard = _SetupWizard(page, state, theme, body)
    wizard.show_welcome_step()

    return ft.View(
        route="/setup",
        bgcolor=theme.bg,
        controls=[
            ft.Container(content=body, alignment=ft.alignment.Alignment.CENTER, expand=True, padding=60),
        ],
    )


class _SetupWizard:
    def __init__(self, page: ft.Page, state: AppState, theme: ThemePreset, body: ft.Column) -> None:
        self.page = page
        self.state = state
        self.theme = theme
        self.body = body
        self._pin_first_entry: str | None = None

    def _set(self, controls: list[ft.Control]) -> None:
        self.body.controls = controls
        self.page.update()

    # -- Step 1: child's name -------------------------------------------------
    def show_welcome_step(self) -> None:
        name_field = ft.TextField(
            hint_text="Type your name here", width=320, text_align=ft.TextAlign.CENTER, autofocus=True,
        )
        error_text = ft.Text("", color=self.theme.danger, size=14)

        def go_next(_e=None) -> None:
            name = (name_field.value or "").strip()
            if not name:
                error_text.value = "Please type your name first! 😊"
                self.page.update()
                return
            self.state.settings.child_name = name
            self.show_parent_pin_step()

        name_field.on_submit = go_next

        self._set([
            ft.Text("Welcome to Python Adventure!", size=32, weight=ft.FontWeight.BOLD, color=self.theme.primary),
            ft.Container(height=20),
            ft.Text("What's your name, explorer?", size=22, weight=ft.FontWeight.BOLD, color=self.theme.text),
            ft.Container(height=10),
            name_field,
            error_text,
            ft.Container(height=10),
            ft.Button(
                "NEXT ➜", width=200, height=56, on_click=go_next,
                style=ft.ButtonStyle(bgcolor=self.theme.primary, color="#FFFFFF"),
            ),
        ])

    # -- Step 2: parent PIN ----------------------------------------------------
    def show_parent_pin_step(self) -> None:
        self._pin_first_entry = None
        pin_field = ft.TextField(
            hint_text="••••", width=200, text_align=ft.TextAlign.CENTER,
            password=True, max_length=4, autofocus=True,
        )
        error_text = ft.Text("", color=self.theme.danger, size=14)

        def submit_pin(_e=None) -> None:
            pin = (pin_field.value or "").strip()
            if not (pin.isdigit() and len(pin) == 4):
                error_text.value = "Please enter exactly 4 digits."
                error_text.color = self.theme.danger
                self.page.update()
                return
            if self._pin_first_entry is None:
                self._pin_first_entry = pin
                pin_field.value = ""
                error_text.value = "Type it again to confirm."
                error_text.color = self.theme.success
                self.page.update()
                return
            if pin != self._pin_first_entry:
                self._pin_first_entry = None
                pin_field.value = ""
                error_text.value = "PINs didn't match. Try again."
                error_text.color = self.theme.danger
                self.page.update()
                return
            self.state.settings.set_parent_pin(pin)
            self.show_finish_step()

        pin_field.on_submit = submit_pin

        def skip(_e=None) -> None:
            self.show_finish_step()

        self._set([
            ft.Text("👋 Grown-ups only", size=28, weight=ft.FontWeight.BOLD, color=self.theme.primary),
            ft.Container(height=10),
            ft.Text("Set a 4-digit PIN to unlock the Parent Area later.", size=16, color=self.theme.text_muted),
            ft.Container(height=20),
            pin_field,
            error_text,
            ft.Container(height=10),
            ft.Button(
                "NEXT ➜", width=200, height=56, on_click=submit_pin,
                style=ft.ButtonStyle(bgcolor=self.theme.primary, color="#FFFFFF"),
            ),
            ft.TextButton("Skip for now", on_click=skip, style=ft.ButtonStyle(color=self.theme.text_muted)),
        ])

    # -- Step 3: finish ----------------------------------------------------------
    def show_finish_step(self) -> None:
        name = self.state.settings.child_name or "Explorer"

        def finish(_e=None) -> None:
            self.state.settings.setup_complete = True
            self.state.save_settings()
            self.page.go("/dashboard")

        self._set([
            ft.Text("🎉", size=60),
            ft.Text(f"All set, {name}!", size=32, weight=ft.FontWeight.BOLD, color=self.theme.primary),
            ft.Text("Your Python Adventure is ready to begin.", size=18, color=self.theme.text),
            ft.Container(height=20),
            ft.Button(
                "▶ START ADVENTURE", width=320, height=64, on_click=finish,
                style=ft.ButtonStyle(bgcolor=self.theme.success, color="#FFFFFF"),
            ),
        ])
