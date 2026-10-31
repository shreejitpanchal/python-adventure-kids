"""The persistent bottom tab bar of the Flet game world: Home, Map,
Mission, Trophies, Codey. Built per screen (views are rebuilt on every
route change) and handed to adventure_kit_flet.scene_view(nav_bar=...),
which mounts it as the View's bottom app bar -- outside the scrolling
content, so it stays put while the screen scrolls, and outside
View.controls, so the control order tests index into is untouched.

Chunky game-world tabs rather than Material's NavigationBar: emoji + label
on a pressable pill, the active one lit in the primary color. Tapping a
tab is an ordinary page.go(), so the back stack in app_window_flet.py
treats it like any other navigation. Flet only.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import flet as ft

from app.ui.color_utils import contrasting_text_color, with_alpha
from app.ui.components.adventure_kit_flet import RADIUS_PILL, accent_gradient, lip_shadow, pressable, soft_shadow
from app.ui.theme_flet import ThemePreset, scaled


@dataclass(frozen=True)
class Tab:
    key: str
    emoji: str
    label: str
    route: str


TABS: tuple[Tab, ...] = (
    Tab("home", "🏠", "Home", "/hub"),
    Tab("map", "🗺️", "Map", "/categories"),
    Tab("mission", "🎯", "Mission", "/dashboard"),
    Tab("trophies", "🏆", "Trophies", "/trophy-room"),
    Tab("codey", "🤖", "Codey", "/closet"),
)
# Routes that belong to a tab without being its root (lit as that tab).
_ROUTE_TABS: dict[str, str] = {
    "/hub": "home",
    "/categories": "map",
    "/projects": "map",
    "/dashboard": "mission",
    "/quiz": "mission",
    "/trophy-room": "trophies",
    "/cards": "trophies",
    "/closet": "codey",
}
BAR_HEIGHT = 84
# Clearance under the tabs for Android's gesture/navigation strip.
BAR_BOTTOM_PADDING = 14


def tab_for_route(route: str) -> Optional[str]:
    """Which tab a route lights, or None for routes outside the tab world
    (lessons, settings, parent area, setup)."""
    if route in _ROUTE_TABS:
        return _ROUTE_TABS[route]
    if route.startswith("/categories/"):
        return "map"
    if route.startswith("/boss/"):
        return "map"
    return None


def build_nav_bar(page, theme: ThemePreset, active: str, *, scale: float = 1.0, state=None) -> ft.BottomAppBar:
    fs = lambda base: scaled(base, scale)  # noqa: E731
    tabs: list[ft.Control] = []
    for tab in TABS:
        is_active = tab.key == active
        text_color = contrasting_text_color(theme.primary) if is_active else theme.text_muted
        pill = ft.Container(
            content=ft.Column(
                [
                    ft.Text(tab.emoji, size=fs(20), text_align=ft.TextAlign.CENTER),
                    ft.Text(tab.label, size=fs(11), weight=ft.FontWeight.BOLD, color=text_color, text_align=ft.TextAlign.CENTER),
                ],
                spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True,
            ),
            gradient=accent_gradient(theme.primary) if is_active else None,
            bgcolor=None if is_active else with_alpha(theme.card, 0.0),
            shadow=lip_shadow(theme.primary, depth=3) if is_active else None,
            border_radius=RADIUS_PILL,
            padding=ft.padding.Padding.symmetric(horizontal=12, vertical=6),
            on_click=(lambda _e, route=tab.route: page.go(route)) if not is_active else None,
            ink=not is_active,
            expand=True,
            data={"kind": "nav_tab", "tab": tab.key, "route": tab.route, "active": is_active},
        )
        if not is_active:
            pressable(pill, page, state=state)
        tabs.append(pill)
    return ft.BottomAppBar(
        content=ft.Row(tabs, spacing=6, alignment=ft.MainAxisAlignment.SPACE_EVENLY, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=theme.card,
        height=BAR_HEIGHT,
        padding=ft.padding.Padding.only(left=10, top=8, right=10, bottom=BAR_BOTTOM_PADDING),
        shadow_color=with_alpha("#000000", 0.2),
        elevation=10,
        data={"kind": "nav_bar", "active": active},
    )
