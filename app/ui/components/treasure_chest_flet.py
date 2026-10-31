"""The Daily Treasure chest on the Learning Hub: one tap per (UTC) day
grants a small XP bonus (ProgressStore.open_daily_chest -- base XP plus a
streak bonus), with a shake-then-pop animation (plus a haptic buzz) and
the reward revealed in place. While closed it rattles every few seconds
(motion_flet.rattle). Already opened today -> a calm 'come back tomorrow'
state, so the card doubles as the daily come-back nudge.

All the rules (once a day, XP amounts, streak bonus) live in the store;
this component only renders and animates. Flet only.
"""
from __future__ import annotations

import math
from typing import Callable, Optional

import flet as ft
import flet.canvas as cv

from app.progress.store import CHEST_MAX_BASE_XP, CHEST_MIN_BASE_XP, ChestReward
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color, with_alpha
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import RADIUS_CARD, accent_gradient, lip_shadow, pressable, soft_shadow
from app.ui.theme_flet import scaled

CLOSED_EMOJI = "🎁"
OPEN_EMOJI = "✨"
CLOSED_TITLE = "Daily Treasure"
CLOSED_SUBTITLE = "Tap to open today's chest!"
OPENED_TITLE = "Treasure collected!"
OPENED_SUBTITLE = "Come back tomorrow for more."


def reward_lines(reward: ChestReward) -> tuple[str, str]:
    """(headline, detail) for a just-opened chest."""
    headline = f"+{reward.total_xp} XP!"
    if reward.leveled_up:
        detail = f"LEVEL UP! You're now Level {reward.level.level} 🎉"
    elif reward.streak_bonus_xp:
        detail = f"{reward.xp} XP + {reward.streak_bonus_xp} streak bonus"
    else:
        detail = "Keep your streak going for a bonus tomorrow!"
    return headline, detail


# -- the treasure wheel -----------------------------------------------------------------
WHEEL_SIZE = 150.0
WHEEL_SPINS = 3
WHEEL_SPIN_MS = 2200
WHEEL_VALUES: tuple[int, ...] = tuple(range(CHEST_MIN_BASE_XP, CHEST_MAX_BASE_XP + 1, 5))
"""One wedge per possible base XP (multiples of 5 between the chest's
min and max), so the pointer can always land on the real reward."""
_WHEEL_COLORS = ("#FF9F1C", "#EC407A", "#7E57C2", "#26C6DA", "#66BB6A", "#FFC93C")


def wheel_angle_for(xp: int) -> float:
    """Rotation (radians) that brings the wedge for `xp` under the pointer
    at the top, after WHEEL_SPINS full turns for the show. Unknown values
    land on the first wedge."""
    index = WHEEL_VALUES.index(xp) if xp in WHEEL_VALUES else 0
    wedge = 2 * math.pi / len(WHEEL_VALUES)
    # Wedge i spans [i*wedge, (i+1)*wedge) clockwise from the top; rotating
    # the wheel by -(center of wedge i) puts that center under the pointer.
    return WHEEL_SPINS * 2 * math.pi - (index + 0.5) * wedge


def wheel_shapes(theme, size: float = WHEEL_SIZE) -> list:
    """Pie wedges with their XP labels, a hub, and a pointer notch."""
    shapes: list = []
    wedge = 360.0 / len(WHEEL_VALUES)
    radius = size / 2
    for index, value in enumerate(WHEEL_VALUES):
        start_deg = -90 + index * wedge
        shapes.append(cv.Arc(
            0, 0, size, size, math.radians(start_deg), math.radians(wedge), use_center=True,
            paint=ft.Paint(color=_WHEEL_COLORS[index % len(_WHEEL_COLORS)], style=ft.PaintingStyle.FILL),
        ))
        mid = math.radians(start_deg + wedge / 2)
        shapes.append(cv.Text(
            radius + math.cos(mid) * radius * 0.65, radius + math.sin(mid) * radius * 0.65, f"{value}",
            style=ft.TextStyle(size=13, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
            alignment=ft.alignment.Alignment.CENTER,
        ))
    shapes.append(cv.Circle(radius, radius, radius * 0.16, paint=ft.Paint(color=theme.card, style=ft.PaintingStyle.FILL)))
    shapes.append(cv.Circle(radius, radius, radius, paint=ft.Paint(color=with_alpha("#000000", 0.25), style=ft.PaintingStyle.STROKE, stroke_width=4)))
    return shapes


def build_treasure_wheel(theme, size: float = WHEEL_SIZE) -> ft.Container:
    """The spinning disc (rotate tweens with animate_rotation) under a fixed
    pointer triangle drawn above it."""
    disc = ft.Container(
        content=cv.Canvas(shapes=wheel_shapes(theme, size), width=size, height=size),
        width=size, height=size, rotate=0.0,
        animate_rotation=ft.Animation(WHEEL_SPIN_MS, ft.AnimationCurve.EASE_OUT),
        data={"kind": "treasure_wheel", "values": list(WHEEL_VALUES)},
    )
    return disc


def build_daily_chest(
    page, state: AppState, *, scale: float,
    on_opened: Optional[Callable[[ChestReward], None]] = None,
) -> ft.Container:
    theme = state.theme
    fs = lambda base: scaled(base, scale)  # noqa: E731
    can_open = state.progress.can_open_daily_chest()
    accent = theme.warning if can_open else theme.card
    text_color = contrasting_text_color(accent) if can_open else theme.text
    muted_color = text_color if can_open else theme.text_muted

    emoji_text = ft.Text(CLOSED_EMOJI if can_open else OPEN_EMOJI, size=fs(40), text_align=ft.TextAlign.CENTER)
    emoji_disc = ft.Container(
        content=emoji_text, width=68, height=68, border_radius=34,
        bgcolor=theme.card if can_open else theme.bg,
        alignment=ft.alignment.Alignment.CENTER,
        shadow=soft_shadow(opacity=0.15, blur=10, dy=4),
    )
    motion.prepare_wobble(emoji_disc)
    motion.prepare_pulse(emoji_disc)

    title_text = ft.Text(
        CLOSED_TITLE if can_open else OPENED_TITLE, size=fs(18), weight=ft.FontWeight.BOLD, color=text_color,
    )
    subtitle_text = ft.Text(CLOSED_SUBTITLE if can_open else OPENED_SUBTITLE, size=fs(13), color=muted_color)

    card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        emoji_disc,
                        # expand=True bounds the text column to the remaining
                        # width so long lines wrap instead of overflowing.
                        ft.Column([title_text, subtitle_text], spacing=4, expand=True),
                    ],
                    spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                wheel_slot,
            ],
            spacing=10,
        ),
        gradient=accent_gradient(accent) if can_open else None,
        bgcolor=None if can_open else theme.card,
        border_radius=RADIUS_CARD, padding=16,
        shadow=[lip_shadow(accent, depth=6), soft_shadow(accent, opacity=0.25)] if can_open else soft_shadow(opacity=0.10),
        data={"kind": "daily_chest", "opened": not can_open},
    )

    # The treasure wheel: hidden until the chest opens, then spins to the
    # wedge matching the reward's base XP (the store already decided it;
    # the wheel just lands there) -- see wheel_angle_for().
    wheel = build_treasure_wheel(theme)
    wheel_slot = ft.Container(content=wheel, visible=False, alignment=ft.alignment.Alignment.CENTER, data={"kind": "wheel_slot"})

    def open_chest(_e) -> None:
        reward = state.progress.open_daily_chest()
        if reward is None:
            # Opened already (e.g. a second tap racing the first) -- just
            # settle into the opened look.
            headline, detail = OPENED_TITLE, OPENED_SUBTITLE
        else:
            headline, detail = reward_lines(reward)
            wheel_slot.visible = True
            wheel.rotate = wheel_angle_for(reward.xp)
        emoji_text.value = OPEN_EMOJI
        title_text.value = headline
        subtitle_text.value = detail
        card.on_click = None
        card.ink = False
        card.data = {"kind": "daily_chest", "opened": True, "reward_xp": reward.total_xp if reward else 0}
        page.update()
        motion.wobble(page, emoji_disc)
        motion.pulse(page, emoji_disc, times=1, big=1.25)
        if reward is not None and state.sound_player is not None:
            state.sound_player.play("level_up" if reward.leveled_up else "success_chime", state.settings)
        if reward is not None and state.haptics is not None:
            state.haptics.reward(state.settings)
        if reward is not None and on_opened is not None:
            on_opened(reward)

    if can_open:
        card.on_click = open_chest
        card.ink = True
        if page is not None:
            # A closed chest rattles now and then -- it wants opening.
            motion.rattle(page, emoji_disc)
            pressable(card, page, state=state)

    return card
