"""Settings screen: pick a color theme from a set of pre-baked presets.

Layout note: uses a wrapping Row of fixed-width cards rather than
ResponsiveRow -- see app/ui/dashboard_flet.py's module docstring for why
(expand=True / ResponsiveRow columns currently render incorrectly in this
Flet version)."""
from __future__ import annotations

import flet as ft

from app.ui.app_state_flet import AppState
from app.ui.theme_flet import THEME_PRESETS, ThemePreset


def build_settings_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme

    header = ft.Row(
        [
            ft.Button(
                "🏠 Menu", on_click=lambda _e: page.go("/dashboard"),
                style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
            ),
            ft.Text("⚙️ Settings", size=26, weight=ft.FontWeight.BOLD, color=theme.primary),
        ],
        spacing=16,
    )

    return ft.View(
        route="/settings",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        padding=24,
        controls=[header, _build_theme_card(page, state)],
    )


def _build_theme_card(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    current_key = state.settings.theme

    options = [
        _build_theme_option(page, state, preset, current_key == preset.key)
        for preset in THEME_PRESETS.values()
    ]

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("🎨 Choose a Theme", size=20, weight=ft.FontWeight.BOLD, color=theme.text),
                ft.Text(
                    "Pick the colors you like best — you can change this anytime.",
                    size=13, color=theme.text_muted,
                ),
                ft.Row(options, wrap=True, spacing=16, run_spacing=16),
            ],
            spacing=8,
        ),
        bgcolor=theme.card, border_radius=20, padding=24,
    )


def _build_theme_option(page: ft.Page, state: AppState, preset: ThemePreset, is_selected: bool) -> ft.Control:
    def select(_e=None) -> None:
        state.apply_theme(preset.key)
        page.go("/settings")

    swatches = ft.Row(
        [
            ft.Container(bgcolor=color, width=28, height=28, border_radius=8)
            for color in (preset.primary, preset.success, preset.warning, preset.danger)
        ],
        spacing=6,
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(f"{preset.icon}  {preset.title}", size=16, weight=ft.FontWeight.BOLD, color=preset.text),
                swatches,
                ft.Button(
                    "✅ Selected" if is_selected else "Select",
                    disabled=is_selected, on_click=select,
                    style=ft.ButtonStyle(bgcolor=preset.primary, color="#FFFFFF"),
                ),
            ],
            spacing=10,
        ),
        bgcolor=preset.bg, border_radius=16, padding=16, width=260,
        border=ft.border.Border.all(3, state.theme.primary if is_selected else preset.card),
    )
