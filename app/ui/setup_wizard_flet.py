"""First-run setup wizard: Codey asks the child's name, then an "all set"
celebration -- see app/ui/parent_dashboard_flet.py for Parent Area.
Settings.preferred_learning_mode is no longer asked here (it stays at its
default, so the Hub leads with the guided path); the Hub still honors the
setting if a settings.json from an older build carries one.

Styled with the game-world kit (app/ui/components/adventure_kit_flet.py):
a full-screen sky, a floating card, chunky buttons and a confetti burst
on the final step."""
from __future__ import annotations

import flet as ft

from app.ui.app_state_flet import AppState
from app.ui.components.adventure_kit_flet import RADIUS_CARD, plain_card, sky_gradient, soft_shadow
from app.ui.components.celebration_flet import build_confetti, play_confetti
from app.ui.components.codey_avatar_flet import build_codey_companion
from app.ui.components.game_button_flet import build_game_button
from app.ui.theme_flet import ThemePreset, scaled


def build_setup_wizard_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    body = ft.Column(spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    wizard = _SetupWizard(page, state, theme, body)
    wizard.show_welcome_step()

    card = plain_card(theme, [body], padding=28, width=400, data={"kind": "setup_card"})
    card.border_radius = RADIUS_CARD + 4
    card.shadow = soft_shadow(opacity=0.2, blur=24, dy=10)

    return ft.View(
        route="/setup",
        bgcolor=theme.bg,
        padding=0,
        controls=[
            ft.Container(
                content=ft.Column(
                    [card], alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO,
                ),
                gradient=sky_gradient(theme), expand=True, alignment=ft.alignment.Alignment.CENTER, padding=24,
            ),
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
        companion = build_codey_companion(
            self.theme, self.scale, "Hi! I'm Codey, your coding buddy. What should I call you?", page=self.page,
        )
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
            self.show_finish_step()

        name_field.on_submit = go_next

        self._set([
            ft.Text("Welcome to Python Adventure!", size=self._fs(28), weight=ft.FontWeight.BOLD, color=self.theme.primary, text_align=ft.TextAlign.CENTER),
            companion.control,
            ft.Container(height=6),
            ft.Text("What's your name, explorer?", size=self._fs(20), weight=ft.FontWeight.BOLD, color=self.theme.text),
            name_field,
            error_text,
            build_game_button("NEXT ➜", go_next, self.page, bgcolor=self.theme.primary, width=220, height=58, size=18, chunky=True),
        ])

    # -- Step 2: finish ----------------------------------------------------------
    def show_finish_step(self) -> None:
        name = self.state.settings.child_name or "Explorer"
        companion = build_codey_companion(
            self.theme, self.scale, f"Let's go, {name}! Your first mission is waiting.", page=self.page,
        )
        confetti = build_confetti()

        def finish(_e=None) -> None:
            self.state.settings.setup_complete = True
            self.state.save_settings()
            self.page.go("/hub")

        self._set([
            confetti,
            ft.Text("🎉", size=self._fs(56)),
            ft.Text(f"All set, {name}!", size=self._fs(30), weight=ft.FontWeight.BOLD, color=self.theme.primary, text_align=ft.TextAlign.CENTER),
            ft.Text("Your Python Adventure is ready to begin.", size=self._fs(16), color=self.theme.text, text_align=ft.TextAlign.CENTER),
            companion.control,
            ft.Container(height=6),
            build_game_button("▶ START ADVENTURE", finish, self.page, bgcolor=self.theme.success, width=300, height=64, size=18, chunky=True),
        ])
        play_confetti(self.page, confetti)
        companion.cheer(self.page)
