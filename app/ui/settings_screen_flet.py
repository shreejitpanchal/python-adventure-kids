"""Settings screen: pick a color theme from a set of pre-baked presets.

Layout note: uses a wrapping Row of fixed-width cards rather than
ResponsiveRow -- see app/ui/dashboard_flet.py's module docstring for why
(expand=True / ResponsiveRow columns currently render incorrectly in this
Flet version)."""
from __future__ import annotations

import flet as ft

from app.ui.app_state_flet import AppState
from app.ui.theme_flet import FONT_FAMILY_PRESETS, THEME_PRESETS, ThemePreset, scaled
from app.version import get_version_label


def build_settings_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731

    header = ft.Row(
        [
            ft.Button(
                "🏠 Menu", on_click=lambda _e: page.go("/dashboard"), height=48,
                style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
            ),
            ft.Text("⚙️ Settings", size=fs(26), weight=ft.FontWeight.BOLD, color=theme.primary),
        ],
        spacing=16,
    )

    return ft.View(
        route="/settings",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        padding=24,
        controls=[
            header, _build_sound_card(page, state), _build_font_card(page, state),
            _build_theme_card(page, state), _build_version_row(state), ft.Container(height=16),
        ],
    )


def _build_version_row(state: AppState) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    return ft.Container(
        content=ft.Text(
            get_version_label(), size=fs(14), weight=ft.FontWeight.BOLD,
            color=theme.text, text_align=ft.TextAlign.CENTER,
        ),
        bgcolor=theme.card, border_radius=12, padding=12, margin=ft.margin.Margin.symmetric(vertical=8),
        alignment=ft.alignment.Alignment.CENTER,
    )


def _build_sound_card(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731

    def on_toggle(e: ft.ControlEvent) -> None:
        state.settings.sound_enabled = e.control.value
        state.save_settings()

    # Not expand=True + MainAxisAlignment.SPACE_BETWEEN to push the switch
    # to the far edge -- see dashboard_flet.py's module docstring and the
    # parent dashboard's summary-row code for why both of those layout
    # tricks are unreliable in this Flet version; a plain spaced Row is
    # the pattern already proven to work everywhere else in this app.
    return ft.Container(
        content=ft.Row(
            [
                ft.Text("🔊 Sound Effects", size=fs(20), weight=ft.FontWeight.BOLD, color=theme.text),
                ft.Switch(value=state.settings.sound_enabled, on_change=on_toggle, active_color=theme.primary),
            ],
            spacing=16,
        ),
        bgcolor=theme.card, border_radius=20, padding=24,
    )


_FONT_SIZE_LABELS = {"small": "Small", "medium": "Medium", "large": "Large", "extra_large": "Extra Large"}
_FONT_FAMILY_LABELS = {"default": "Playful", "classic": "Classic"}


def _build_font_card(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731

    def select(family_key: str | None = None, size_key: str | None = None):
        def handler(_e=None) -> None:
            state.apply_font(
                family_key or state.settings.font_family,
                size_key or state.settings.font_size,
            )
            # Same rebuild-in-place pattern as the theme card's select() --
            # see its comment for why page.go("/settings") wouldn't repaint.
            page.views.clear()
            page.views.append(build_settings_view(page, state))
            page.theme = ft.Theme(font_family=state.font_family)
            page.dark_theme = ft.Theme(font_family=state.font_family)
            page.update()
        return handler

    current_size = state.settings.font_size
    size_buttons = [
        ft.Button(
            label, on_click=select(size_key=key), height=40,
            disabled=current_size == key,
            style=ft.ButtonStyle(
                bgcolor=theme.primary if current_size == key else theme.text_muted, color="#FFFFFF",
            ),
        )
        for key, label in _FONT_SIZE_LABELS.items()
    ]

    current_family = state.settings.font_family
    family_buttons = [
        ft.Button(
            label, on_click=select(family_key=key), height=40,
            disabled=current_family == key,
            style=ft.ButtonStyle(
                bgcolor=theme.primary if current_family == key else theme.text_muted, color="#FFFFFF",
                text_style=ft.TextStyle(font_family=FONT_FAMILY_PRESETS[key]),
            ),
        )
        for key, label in _FONT_FAMILY_LABELS.items()
    ]

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("🔤 Text Size & Font", size=fs(20), weight=ft.FontWeight.BOLD, color=theme.text),
                ft.Text(
                    "Make text bigger or change the style — great for reading on a tablet.",
                    size=fs(13), color=theme.text_muted,
                ),
                ft.Text("Size", size=fs(13), color=theme.text_muted),
                ft.Row(size_buttons, wrap=True, spacing=8),
                ft.Text("Style", size=fs(13), color=theme.text_muted),
                ft.Row(family_buttons, wrap=True, spacing=8),
            ],
            spacing=8,
        ),
        bgcolor=theme.card, border_radius=20, padding=24,
    )


def _build_theme_card(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    current_key = state.settings.theme
    player_level = state.progress.get_player_level().level

    options = [
        _build_theme_option(page, state, preset, current_key == preset.key, player_level >= preset.min_level)
        for preset in THEME_PRESETS.values()
    ]

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("🎨 Choose a Theme", size=fs(20), weight=ft.FontWeight.BOLD, color=theme.text),
                ft.Text(
                    "Pick the colors you like best — you can change this anytime.",
                    size=fs(13), color=theme.text_muted,
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
                    size=scaled(16, state.font_scale), weight=ft.FontWeight.BOLD,
                    color=preset.text if unlocked else preset.text_muted,
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
