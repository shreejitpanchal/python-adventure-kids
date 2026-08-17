"""Learning Hub: the new top-of-hierarchy screen for the Flet app -- a
choice of four ways into the content (guided path, two Code Cracker
tracks, and projects) instead of dropping straight into "Today's Mission"
the way the old dashboard did. All status text is computed once in
app/engine/hub_status.py and just rendered here; this screen never
recomputes progress numbers itself.

Settings and Parent Area live in this screen's header, not the Dashboard's
-- this is the true top of the navigation hierarchy, so they only need one
home.

Layout note: same vertical-Column-of-cards pattern as dashboard_flet.py /
settings_screen_flet.py -- see dashboard_flet.py's module docstring for
why `expand=True` Rows are avoided in this Flet version.
"""
from __future__ import annotations

import flet as ft

from app.engine.hub_status import compute_hub_status
from app.ui.app_state_flet import AppState
from app.ui.theme_flet import scaled

# Card key -> concrete route. Shared by both the resume banner and the
# cards themselves, and matches Settings.last_learning_route's semantic
# values (see app/config/settings.py + app/engine/hub_status.py).
_ROUTES: dict[str, str] = {
    "guided": "/dashboard",
    "code_crackers": "/categories/code_crackers",
    "advanced_code_crackers": "/categories/advanced_code_crackers",
    "projects": "/projects",
}


def build_learning_hub_view(page: ft.Page, state: AppState) -> ft.View:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    hub_status = compute_hub_status(state.lesson_engine, state.progress, state.settings)

    controls: list[ft.Control] = [_build_header(page, state)]

    if hub_status.resume_label is not None:
        controls.append(ft.Container(height=12))
        controls.append(_build_resume_banner(page, state, hub_status.resume_label))

    controls.append(ft.Container(height=16))
    controls.extend(_build_cards(page, state, hub_status))

    return ft.View(
        route="/hub",
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        # Extra bottom clearance (vs. a plain uniform padding) -- on Android,
        # the system gesture/navigation bar otherwise overlaps the last
        # control on every scrollable screen (reported: the Hub's last card
        # and Parent Area's Reset Progress button both cut off at the
        # bottom). Applied to every scrollable Flet View, not just this one.
        padding=ft.padding.Padding.only(left=24, top=24, right=24, bottom=80),
        controls=controls,
    )


def _build_header(page: ft.Page, state: AppState) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    name = state.settings.child_name or "Explorer"

    return ft.Column(
        [
            ft.Row(
                [
                    ft.Image(src="main-icon.png", width=40, height=40),
                    ft.Text("Python Adventure", size=fs(22), weight=ft.FontWeight.BOLD, color=theme.primary),
                ],
                spacing=8,
            ),
            ft.Row(
                [
                    ft.Button(
                        "⚙️ Settings", on_click=lambda _e: page.go("/settings"), height=48,
                        style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
                    ),
                    ft.Button(
                        "👋 Parent Area", on_click=lambda _e: page.go("/parent"), height=48,
                        style=ft.ButtonStyle(bgcolor=theme.text_muted, color="#FFFFFF"),
                    ),
                ],
                spacing=8, wrap=True,
            ),
            ft.Text(f"Welcome back, {name}!", size=fs(20), weight=ft.FontWeight.BOLD, color=theme.text),
        ],
        spacing=10,
    )


def _build_resume_banner(page: ft.Page, state: AppState, resume_label: str) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731
    route_key = state.settings.last_learning_route
    target_route = _ROUTES.get(route_key, "/hub")

    def on_click(_e: ft.ControlEvent) -> None:
        page.go(target_route)

    return ft.Container(
        content=ft.Text(f"↩ {resume_label}", size=fs(14), weight=ft.FontWeight.BOLD, color="#FFFFFF"),
        bgcolor=theme.primary, border_radius=14, padding=14,
        on_click=on_click, ink=True,
    )


# Card definitions in fixed relative order. Each entry: (key, title,
# subtitle, hub_status attribute name, route).
_CARD_DEFS: list[tuple[str, str, str, str, str]] = [
    (
        "guided", "🚀 Start Learning Python",
        "A guided path for beginners. Continue your next lesson.",
        "guided_status", "/dashboard",
    ),
    (
        "code_crackers", "🐛 Fix Code Cracker Puzzles",
        "Find and fix bugs in short Python programs.",
        "cracker_status", "/categories/code_crackers",
    ),
    (
        "advanced_code_crackers", "🧠 Advanced Code Crackers",
        "Tricky real-world Python bugs for experienced coders.",
        "advanced_cracker_status", "/categories/advanced_code_crackers",
    ),
    (
        "projects", "🛠️ Build a Project",
        "Games, art, adventures, and coding challenges.",
        "project_status", "/projects",
    ),
]


# Settings.preferred_learning_mode's semantic keys (guided/projects/
# crackers/advanced -- set during the setup wizard, see setup_wizard_flet.py)
# map onto the Hub's own card keys, which mirror last_learning_route's
# vocabulary instead (guided/code_crackers/advanced_code_crackers/projects)
# -- "crackers" means the (non-advanced) Code Crackers card.
_PREFERRED_MODE_TO_CARD_KEY: dict[str, str] = {
    "guided": "guided",
    "projects": "projects",
    "crackers": "code_crackers",
    "advanced": "advanced_code_crackers",
}


def _build_cards(page: ft.Page, state: AppState, hub_status) -> list[ft.Control]:
    preferred = _PREFERRED_MODE_TO_CARD_KEY.get(state.settings.preferred_learning_mode, "guided")

    ordered_defs = sorted(
        _CARD_DEFS, key=lambda card_def: 0 if card_def[0] == preferred else 1,
    )

    cards: list[ft.Control] = []
    for key, title, subtitle, status_attr, route in ordered_defs:
        status = getattr(hub_status, status_attr)
        featured = key == preferred
        cards.append(_build_card(page, state, key, title, subtitle, status, route, featured))
        cards.append(ft.Container(height=12))
    if cards:
        cards.pop()  # drop the trailing spacer
    return cards


def _build_card(
    page: ft.Page, state: AppState, key: str, title: str, subtitle: str,
    status: str, route: str, featured: bool,
) -> ft.Control:
    theme = state.theme
    fs = lambda base: scaled(base, state.font_scale)  # noqa: E731

    def on_click(_e: ft.ControlEvent) -> None:
        state.settings.last_learning_route = key
        state.save_settings()
        page.go(route)

    title_size = fs(24) if featured else fs(18)
    subtitle_size = fs(14) if featured else fs(13)
    status_size = fs(13) if featured else fs(12)
    padding = 28 if featured else 18

    return ft.Container(
        content=ft.Column(
            [
                ft.Text(title, size=title_size, weight=ft.FontWeight.BOLD, color=theme.text),
                ft.Text(subtitle, size=subtitle_size, color=theme.text_muted),
                ft.Text(status, size=status_size, color=theme.primary, weight=ft.FontWeight.BOLD),
            ],
            spacing=6,
        ),
        bgcolor=theme.card, border_radius=20, padding=padding,
        border=ft.border.Border.all(3, theme.primary) if featured else None,
        on_click=on_click, ink=True,
    )
