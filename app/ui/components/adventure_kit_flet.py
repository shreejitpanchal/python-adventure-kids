"""The game-world visual kit shared by the Flet core-loop screens (Hub,
Dashboard, Adventure Map, Category Levels, Lesson): sky-gradient hero
headers, chunky 3D-lipped shapes, accent-gradient cards, stat chips, the
XP "power bar", and the standard scrolling View wrapper -- so the screens
share one look instead of each hand-picking radii, shadows and paddings.

Flet only. Everything here is a plain composition of ft.Container /
ft.Row / ft.Column / ft.Text using the same properties the rest of the
Flet UI already relies on (gradient, shadow, border_radius, offsets) --
no extension controls, which don't render in the `flet run` live-preview
client on Android (see app_window_flet.py on flet_audio).

Key controls carry a `data={"kind": ..., ...}` dict so tests (and any
future tooling) can find them by role via find_by_kind() instead of
depending on positional indexes into a screen's control tree.
"""
from __future__ import annotations

import asyncio
from typing import Callable, Iterable, Optional

import flet as ft

from app.ui.color_utils import contrasting_text_color, darken, lighten, with_alpha
from app.ui.theme_flet import ThemePreset, scaled, sky_colors

RADIUS_CARD = 24
RADIUS_PILL = 40
SCREEN_PADDING = 20
# Extra bottom clearance so the last control isn't hidden behind Android's
# gesture/navigation bar -- see learning_hub_flet.py's history for why.
BOTTOM_CLEARANCE = 88


# -- gradients & shadows -----------------------------------------------------------
def sky_gradient(theme: ThemePreset) -> ft.LinearGradient:
    top, bottom = sky_colors(theme)
    return ft.LinearGradient(
        begin=ft.alignment.Alignment.TOP_CENTER, end=ft.alignment.Alignment.BOTTOM_CENTER,
        colors=[top, bottom],
    )


def accent_gradient(color: str) -> ft.LinearGradient:
    """A lit-from-the-top-left version of one accent color -- what makes a
    card or node read as a solid, rounded object instead of a flat fill."""
    return ft.LinearGradient(
        begin=ft.alignment.Alignment.TOP_LEFT, end=ft.alignment.Alignment.BOTTOM_RIGHT,
        colors=[lighten(color, 0.18), darken(color, 0.10)],
    )


def soft_shadow(color: str = "#000000", *, opacity: float = 0.16, blur: float = 18, dy: float = 8) -> ft.BoxShadow:
    return ft.BoxShadow(blur_radius=blur, spread_radius=0, color=with_alpha(color, opacity), offset=ft.Offset(0, dy))


def lip_shadow(color: str, *, depth: float = 5) -> ft.BoxShadow:
    """A hard, unblurred shadow straight below -- the 'thick edge' that
    makes a button or node look like a physical block you can press."""
    return ft.BoxShadow(blur_radius=0, spread_radius=0, color=darken(color, 0.35), offset=ft.Offset(0, depth))


# -- layout wrappers -----------------------------------------------------------------
def scene_view(route: str, theme: ThemePreset, controls: list[ft.Control]) -> ft.View:
    """The standard scrolling screen: flat theme bg, phone-friendly side
    padding, extra bottom clearance for Android's navigation bar."""
    return ft.View(
        route=route,
        bgcolor=theme.bg,
        scroll=ft.ScrollMode.AUTO,
        padding=ft.padding.Padding.only(
            left=SCREEN_PADDING, top=12, right=SCREEN_PADDING, bottom=BOTTOM_CLEARANCE,
        ),
        controls=controls,
    )


def hero_header(
    theme: ThemePreset, *, title: str, scale: float,
    buttons: Iterable[ft.Control] = (), companion: Optional[ft.Control] = None,
    icon_src: Optional[str] = "main-icon.png", title_color: Optional[str] = None,
) -> ft.Container:
    """The sky band at the top of a screen: app icon + title, a wrapping row
    of pill buttons, and (optionally) Codey with a speech bubble."""
    fs = lambda base: scaled(base, scale)  # noqa: E731
    title_row_children: list[ft.Control] = []
    if icon_src:
        title_row_children.append(ft.Image(src=icon_src, width=40, height=40))
    # expand=True lets the title wrap onto a second line at large font
    # scales instead of overflowing the screen edge.
    title_row_children.append(
        ft.Text(title, size=fs(24), weight=ft.FontWeight.BOLD, color=title_color or theme.primary, expand=True)
    )
    children: list[ft.Control] = [ft.Row(title_row_children, spacing=10)]
    buttons = list(buttons)
    if buttons:
        children.append(ft.Row(buttons, spacing=8, run_spacing=8, wrap=True))
    if companion is not None:
        children.append(companion)
    return ft.Container(
        content=ft.Column(children, spacing=14),
        gradient=sky_gradient(theme),
        padding=ft.padding.Padding.only(left=SCREEN_PADDING, top=20, right=SCREEN_PADDING, bottom=22),
        border_radius=RADIUS_CARD + 4,
        shadow=soft_shadow(opacity=0.14, blur=16, dy=6),
        data={"kind": "hero_header", "title": title},
    )


def pill_button(
    label: str, on_click: Callable, *, bgcolor: str, color: Optional[str] = None, height: int = 44,
) -> ft.Button:
    return ft.Button(
        label, on_click=on_click, height=height,
        style=ft.ButtonStyle(bgcolor=bgcolor, color=color or contrasting_text_color(bgcolor)),
    )


def section_title(theme: ThemePreset, text: str, scale: float) -> ft.Text:
    return ft.Text(text, size=scaled(18, scale), weight=ft.FontWeight.BOLD, color=theme.text)


def spacer(height: int = 14) -> ft.Container:
    return ft.Container(height=height)


# -- small building blocks -----------------------------------------------------------
def emoji_badge(emoji: str, *, size: int = 56, bgcolor: str, scale: float = 1.0, lip: bool = True) -> ft.Container:
    """A round, chunky disc with one big emoji -- the app's stand-in for
    illustrated icons (everything here is emoji-only, no bundled art)."""
    return ft.Container(
        content=ft.Text(emoji, size=scaled(round(size * 0.5), scale), text_align=ft.TextAlign.CENTER),
        width=size, height=size, border_radius=size / 2,
        gradient=accent_gradient(bgcolor),
        shadow=lip_shadow(bgcolor, depth=4) if lip else None,
        alignment=ft.alignment.Alignment.CENTER,
    )


def stat_chip(
    theme: ThemePreset, icon: str, label: str, scale: float, *,
    accent: Optional[str] = None, kind: str = "stat_chip",
) -> ft.Container:
    """"🔥 3 day streak"-style pill. `accent` tints the pill; the default is
    the theme card color so a row of chips reads as a HUD strip."""
    fs = lambda base: scaled(base, scale)  # noqa: E731
    bg = accent or theme.card
    text_color = theme.text if accent is None else contrasting_text_color(bg)
    return ft.Container(
        content=ft.Row(
            [ft.Text(icon, size=fs(16)), ft.Text(label, size=fs(14), weight=ft.FontWeight.BOLD, color=text_color)],
            spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=bg, border_radius=RADIUS_PILL,
        padding=ft.padding.Padding.symmetric(horizontal=14, vertical=8),
        shadow=soft_shadow(opacity=0.10, blur=10, dy=4),
        data={"kind": kind, "label": label},
    )


def power_bar(
    theme: ThemePreset, ratio: float, *, color: Optional[str] = None,
    width: int = 260, height: int = 18,
) -> ft.Container:
    """A chunky progress bar whose fill grows with an implicit animation
    (Container.animate) whenever its width changes -- set ratio 0 first and
    the real ratio a beat later (see animate_power_bar) for a fill-up
    effect on arrival. data carries the ratio for tests."""
    ratio = max(0.0, min(1.0, ratio))
    fill_color = color or theme.success
    fill = ft.Container(
        width=round(width * ratio), height=height, border_radius=height / 2,
        gradient=accent_gradient(fill_color),
        animate=ft.Animation(700, ft.AnimationCurve.EASE_OUT),
    )
    track = ft.Container(
        content=ft.Row([fill], spacing=0),
        width=width, height=height, border_radius=height / 2,
        bgcolor=with_alpha(theme.text_muted, 0.22),
        data={"kind": "power_bar", "ratio": ratio, "width": width},
    )
    return track


def power_bar_fill(bar: ft.Container) -> ft.Container:
    return bar.content.controls[0]


async def _grow_fill(page, fill: ft.Container, target_width: int) -> None:
    await asyncio.sleep(0.15)
    fill.width = target_width
    page.update()


def play_power_bar(page, bar: ft.Container) -> bool:
    """Fill-up-on-arrival: parks the fill at zero width, then restores the
    real width a beat later so Container.animate tweens it. Leaves the bar
    at its real width when the page can't schedule tasks."""
    fill = power_bar_fill(bar)
    target_width = fill.width
    run_task = getattr(page, "run_task", None)
    if run_task is None or not target_width:
        return False
    fill.width = 0
    run_task(_grow_fill, page, fill, target_width)
    return True


def hero_card(
    theme: ThemePreset, *, accent: str, children: list[ft.Control],
    on_click: Optional[Callable] = None, data: Optional[dict] = None, padding: int = 20,
    featured: bool = False,
) -> ft.Container:
    """A gradient 'world tile': the big colorful card every mode/mission
    lives on. Featured tiles get a bright rim so the one to tap is obvious."""
    return ft.Container(
        content=ft.Column(children, spacing=8),
        gradient=accent_gradient(accent),
        border_radius=RADIUS_CARD, padding=padding,
        shadow=[lip_shadow(accent, depth=6), soft_shadow(accent, opacity=0.25)],
        border=ft.border.Border.all(3, with_alpha("#FFFFFF", 0.85)) if featured else None,
        on_click=on_click, ink=on_click is not None,
        data=data,
    )


def plain_card(theme: ThemePreset, children: list[ft.Control], *, data: Optional[dict] = None, padding: int = 18) -> ft.Container:
    """A neutral, theme-card-colored panel with a soft drop shadow -- for
    content that shouldn't compete with the hero tiles."""
    return ft.Container(
        content=ft.Column(children, spacing=10),
        bgcolor=theme.card, border_radius=RADIUS_CARD, padding=padding,
        shadow=soft_shadow(opacity=0.12),
        data=data,
    )


# -- lookup ------------------------------------------------------------------------------
def iter_controls(root) -> Iterable:
    """Depth-first walk over a control tree via .controls and .content."""
    yield root
    for child in list(getattr(root, "controls", None) or []):
        yield from iter_controls(child)
    content = getattr(root, "content", None)
    if content is not None and not isinstance(content, (str, int, float)):
        yield from iter_controls(content)


def find_by_kind(root, kind: str) -> list:
    """Every control under `root` whose data is a dict with data["kind"] == kind."""
    return [
        control for control in iter_controls(root)
        if isinstance(getattr(control, "data", None), dict) and control.data.get("kind") == kind
    ]
