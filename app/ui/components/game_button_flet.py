"""A tactile, animated button -- Flet only, no CTk equivalent (CustomTkinter
has no scale-transform/implicit-animation primitives).

Wraps a plain ft.Container in a GestureDetector so a tap visibly squeezes
the button down and springs it back, instead of an instant, static click.
This Flet version has no separate "AnimatedContainer" control -- scale and
animate_scale live directly on the base LayoutControl mixin that Container
already inherits, so a plain Container is enough.

`chunky=True` adds the game-world look from adventure_kit_flet: a gradient
face over a hard, unblurred shadow straight below (the "thick edge" of a
physical block), so pressing it reads as pushing a real button in.
"""
from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.ui.components.adventure_kit_flet import accent_gradient, lip_shadow

_SQUEEZE_SCALE = 0.92
_ANIMATION_MS = 150


def build_game_button(
    text: str,
    on_click: Callable[[ft.ControlEvent], None],
    page: ft.Page,
    *,
    bgcolor: str,
    text_color: str = "#FFFFFF",
    width: Optional[int] = None,
    height: int = 56,
    size: int = 16,
    chunky: bool = False,
    radius: int = 12,
) -> ft.GestureDetector:
    """`page` is required (not the container's own .update()) because a
    control's own .update() raises unless it's already attached to a live
    page tree -- the same reason app/games/game_canvas_flet.py always calls
    page.update() instead of updating itself."""
    container = ft.Container(
        content=ft.Text(text, color=text_color, weight=ft.FontWeight.BOLD, size=size, text_align=ft.TextAlign.CENTER),
        alignment=ft.alignment.Alignment.CENTER,
        bgcolor=None if chunky else bgcolor,
        gradient=accent_gradient(bgcolor) if chunky else None,
        shadow=lip_shadow(bgcolor, depth=6) if chunky else None,
        padding=ft.padding.Padding.symmetric(vertical=14, horizontal=28),
        border_radius=radius if not chunky else max(radius, 18),
        scale=1.0,
        animate_scale=ft.Animation(_ANIMATION_MS, ft.AnimationCurve.EASE_OUT),
        width=width,
        height=height,
        data={"kind": "game_button", "text": text},
    )

    def _squeeze(_e: ft.ControlEvent) -> None:
        container.scale = _SQUEEZE_SCALE
        page.update()

    def _release(_e: ft.ControlEvent) -> None:
        container.scale = 1.0
        page.update()

    return ft.GestureDetector(
        content=container,
        on_tap_down=_squeeze,
        on_tap_up=_release,
        on_tap_cancel=_release,
        on_tap=on_click,
    )
