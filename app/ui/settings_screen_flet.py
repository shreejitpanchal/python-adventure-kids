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
                "🏠 Menu", on_click=lambda _e: page.go("/dashboard"), height=48,
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
    player_level = state.progress.get_player_level().level

    options = [
        _build_theme_option(page, state, preset, current_key == preset.key, player_level >= preset.min_level)
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


def _build_theme_option(
    page: ft.Page, state: AppState, preset: ThemePreset, is_selected: bool, unlocked: bool,
) -> ft.Control:
    def select(_e=None) -> None:
        if state.progress.get_player_level().level < preset.min_level:
            return  # defense in depth -- the button should already be disabled
        state.apply_theme(preset.key)
        # Not page.go("/settings") -- Flet's own routing drops a RouteChangeEvent
        # whose route matches the last-seen one (Page.before_event(), page.py),
        # so navigating to the route we're already on is a silent no-op: the
        # view stays built with the old theme's colors until some other route
        # actually changes. Rebuild the view and reapply the page-level theme
        # bits in place instead, the same way app_window_flet.route_change() does.
        page.views.clear()
        page.views.append(build_settings_view(page, state))
        page.bgcolor = state.theme.bg
        page.theme_mode = ft.ThemeMode.DARK if state.theme.is_dark else ft.ThemeMode.LIGHT
        page.update()

    swatch_colors = (
        (preset.primary, preset.success, preset.warning, preset.danger) if unlocked
        else (preset.text_muted,) * 4
    )
    swatches = ft.Row(
        [ft.Container(bgcolor=color, width=28, height=28, border_radius=8) for color in swatch_colors],
        spacing=6,
    )

    if not unlocked:
        button_text = f"🔒 Unlocks at Level {preset.min_level}"
    else:
        button_text = "✅ Selected" if is_selected else "Select"

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    f"{preset.icon}  {preset.title}" if unlocked else f"🔒  {preset.title}",
                    size=16, weight=ft.FontWeight.BOLD, color=preset.text if unlocked else preset.text_muted,
                ),
                swatches,
                ft.Button(
                    button_text,
                    disabled=is_selected or not unlocked, on_click=select, height=48,
                    style=ft.ButtonStyle(bgcolor=preset.primary if unlocked else preset.text_muted, color="#FFFFFF"),
                ),
            ],
            spacing=10,
        ),
        bgcolor=preset.bg, border_radius=16, padding=16, width=260,
        border=ft.border.Border.all(3, state.theme.primary if is_selected else preset.card),
    )
