"""A full-screen, animated "mission accomplished" overlay -- Flet only, no
CTk equivalent (see game_button_flet.py's module docstring for why).

Replaces a plain always-visible-once-toggled reward Container with a
ft.Stack layer: a dimmed background, a handful of floating particles, and
a badge card that springs in via scale animation. Built once per lesson
screen and toggled via the returned VictoryOverlayHandle -- the caller
(app/ui/lesson_screen_flet.py) still just sets reward_text.value/
badge_text.value and calls .show(), matching the shape of the plain
reward_card it replaces so the rest of the lesson flow (and its tests)
didn't need to change.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

import flet as ft

from app.ui.components.game_button_flet import build_game_button

_BADGE_CARD_COLOR = "#FFF3D0"
_PARTICLE_COUNT = 18
_PARTICLE_COLORS_KEY = ("star", "success", "primary", "warning")


@dataclass
class VictoryOverlayHandle:
    overlay: ft.Stack
    reward_text: ft.Text
    badge_text: ft.Text
    show: Callable[[], None]
    hide: Callable[[], None]


def build_victory_overlay(page: ft.Page, theme, on_continue: Callable[[ft.ControlEvent], None]) -> VictoryOverlayHandle:
    particle_colors = [getattr(theme, key) for key in _PARTICLE_COLORS_KEY]

    dim_background = ft.Container(
        bgcolor="#000000", opacity=0.0, expand=True,
        animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
    )

    particles = [
        ft.Container(
            bgcolor=random.choice(particle_colors),
            width=random.randint(6, 14), height=random.randint(6, 14),
            border_radius=50,
            left=random.uniform(20, 380), top=random.uniform(-30, 0),
            animate_position=ft.Animation(1100, ft.AnimationCurve.EASE_OUT),
        )
        for _ in range(_PARTICLE_COUNT)
    ]

    # contrasting_text_color isn't imported here to keep this component
    # theme-agnostic beyond the four accent colors above; the badge card's
    # background is fixed (matches the reward card it replaces), so its
    # text is fixed dark too -- see the #2547 fix this mirrors.
    reward_text = ft.Text("", size=22, weight=ft.FontWeight.BOLD, color="#232323", text_align=ft.TextAlign.CENTER)
    badge_text = ft.Text("", size=16, color="#232323", text_align=ft.TextAlign.CENTER)

    continue_button = build_game_button(
        "ONWARD ➜", on_continue, page, bgcolor=theme.primary, width=240, height=56,
    )

    badge_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("🏆", size=48, text_align=ft.TextAlign.CENTER),
                reward_text,
                badge_text,
                ft.Container(height=6),
                continue_button,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8,
        ),
        bgcolor=_BADGE_CARD_COLOR, padding=32, border_radius=24, width=340,
        scale=0.0,
        animate_scale=ft.Animation(500, ft.AnimationCurve.ELASTIC_OUT),
    )

    overlay = ft.Stack(
        [dim_background, *particles, ft.Container(content=badge_card, alignment=ft.alignment.Alignment.CENTER, expand=True)],
        expand=True,
        visible=False,
    )

    def show() -> None:
        overlay.visible = True
        dim_background.opacity = 0.85
        badge_card.scale = 1.0
        for particle in particles:
            particle.top = random.uniform(120, 480)
            particle.left = random.uniform(20, 380)
        page.update()

    def hide() -> None:
        overlay.visible = False
        dim_background.opacity = 0.0
        badge_card.scale = 0.0
        for particle in particles:
            particle.top = random.uniform(-30, 0)
        page.update()

    return VictoryOverlayHandle(overlay=overlay, reward_text=reward_text, badge_text=badge_text, show=show, hide=hide)
