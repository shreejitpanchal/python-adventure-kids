"""First-run setup wizard: just the child's name and, optionally, a
preferred learning mode -- see app/ui/parent_dashboard_flet.py for Parent Area."""
from __future__ import annotations

import flet as ft

from app.ui.app_state_flet import AppState
from app.ui.theme_flet import ThemePreset, scaled


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
        self.scale = state.font_scale

    def _fs(self, base_size: int) -> int:
        """Scaled font size -- see AppState.font_scale / app/ui/theme_flet.py."""
        return scaled(base_size, self.scale)

    def _set(self, controls: list[ft.Control]) -> None:
        self.body.controls = controls
        self.page.update()

    # -- Step 1: child's name -------------------------------------------------
    def show_welcome_step(self) -> None:
        name_field = ft.TextField(
            hint_text="Type your name here", width=320, text_align=ft.TextAlign.CENTER, autofocus=True,
        )
        error_text = ft.Text("", color=self.theme.danger, size=self._fs(14))

        def go_next(_e=None) -> None:
            name = (name_field.value or "").strip()
            if not name:
                error_text.value = "Please type your name first! 😊"
                self.page.update()
                return
            self.state.settings.child_name = name
            self.show_mode_step()

        name_field.on_submit = go_next

        self._set([
            ft.Text("Welcome to Python Adventure!", size=self._fs(32), weight=ft.FontWeight.BOLD, color=self.theme.primary),
            ft.Container(height=20),
            ft.Text("What's your name, explorer?", size=self._fs(22), weight=ft.FontWeight.BOLD, color=self.theme.text),
            ft.Container(height=10),
            name_field,
            error_text,
            ft.Container(height=10),
            ft.Button(
                "NEXT ➜", width=200, height=56, on_click=go_next,
                style=ft.ButtonStyle(bgcolor=self.theme.primary, color="#FFFFFF"),
            ),
        ])

    # -- Step 2: preferred learning mode (skippable) -----------------------------
    def show_mode_step(self) -> None:
        """Sets Settings.preferred_learning_mode, which the Learning Hub
        (app/ui/learning_hub_flet.py) uses to decide which of its five
        cards renders first/largest. Purely a preference nudge -- every
        mode stays reachable from the Hub regardless of what's picked (or
        skipped) here, so getting it "wrong" costs nothing."""
        options = [
            ("Learn Python from the beginning", "guided"),
            ("Make games and creative projects", "projects"),
            ("Practise coding puzzles", "crackers"),
            ("I already know some Python", "advanced"),
        ]

        def choose(mode_key: str):
            def handler(_e=None) -> None:
                self.state.settings.preferred_learning_mode = mode_key
                self.show_finish_step()
            return handler

        def skip(_e=None) -> None:
            self.show_finish_step()

        option_buttons = [
            ft.Button(
                label, width=320, height=56, on_click=choose(mode_key),
                style=ft.ButtonStyle(bgcolor=self.theme.primary, color="#FFFFFF"),
            )
            for label, mode_key in options
        ]

        self._set([
            ft.Text("What sounds most fun today?", size=self._fs(28), weight=ft.FontWeight.BOLD, color=self.theme.primary),
            ft.Container(height=10),
            ft.Column(option_buttons, spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=10),
            ft.TextButton(
                "Skip for now", on_click=skip,
                style=ft.ButtonStyle(color=self.theme.text_muted),
            ),
        ])

    # -- Step 3: finish ----------------------------------------------------------
    def show_finish_step(self) -> None:
        name = self.state.settings.child_name or "Explorer"

        def finish(_e=None) -> None:
            self.state.settings.setup_complete = True
            self.state.save_settings()
            self.page.go("/hub")

        self._set([
            ft.Text("🎉", size=self._fs(60)),
            ft.Text(f"All set, {name}!", size=self._fs(32), weight=ft.FontWeight.BOLD, color=self.theme.primary),
            ft.Text("Your Python Adventure is ready to begin.", size=self._fs(18), color=self.theme.text),
            ft.Container(height=20),
            ft.Button(
                "▶ START ADVENTURE", width=320, height=64, on_click=finish,
                style=ft.ButtonStyle(bgcolor=self.theme.success, color="#FFFFFF"),
            ),
        ])
