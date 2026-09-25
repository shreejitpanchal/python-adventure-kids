"""The Daily Treasure chest on the Learning Hub: one tap per (UTC) day
grants a small XP bonus (ProgressStore.open_daily_chest -- base XP plus a
streak bonus), with a shake-then-pop animation and the reward revealed in
place. Already opened today -> a calm 'come back tomorrow' state, so the
card doubles as the daily come-back nudge.

All the rules (once a day, XP amounts, streak bonus) live in the store;
this component only renders and animates. Flet only.
"""
from __future__ import annotations

from typing import Callable, Optional

import flet as ft

from app.progress.store import ChestReward
from app.ui.app_state_flet import AppState
from app.ui.color_utils import contrasting_text_color
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import RADIUS_CARD, accent_gradient, lip_shadow, soft_shadow
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
        content=ft.Row(
            [
                emoji_disc,
                # expand=True bounds the text column to the remaining width
                # so long lines wrap instead of overflowing.
                ft.Column([title_text, subtitle_text], spacing=4, expand=True),
            ],
            spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        gradient=accent_gradient(accent) if can_open else None,
        bgcolor=None if can_open else theme.card,
        border_radius=RADIUS_CARD, padding=16,
        shadow=[lip_shadow(accent, depth=6), soft_shadow(accent, opacity=0.25)] if can_open else soft_shadow(opacity=0.10),
        data={"kind": "daily_chest", "opened": not can_open},
    )

    def open_chest(_e) -> None:
        reward = state.progress.open_daily_chest()
        if reward is None:
            # Opened already (e.g. a second tap racing the first) -- just
            # settle into the opened look.
            headline, detail = OPENED_TITLE, OPENED_SUBTITLE
        else:
            headline, detail = reward_lines(reward)
        emoji_text.value = OPEN_EMOJI
        title_text.value = headline
        subtitle_text.value = detail
        card.on_click = None
        card.ink = False
        card.data = {"kind": "daily_chest", "opened": True, "reward_xp": reward.total_xp if reward else 0}
        page.update()
        motion.wobble(page, emoji_disc)
        motion.pulse(page, emoji_disc, times=1, big=1.25)
        if reward is not None and on_opened is not None:
            on_opened(reward)

    if can_open:
        card.on_click = open_chest
        card.ink = True
        if page is not None:
            motion.pulse(page, emoji_disc, times=3, big=1.1)

    return card
