"""Day-streak presentation for the Flet game-world UI: the flame chip that
grows with the streak, and the once-a-day welcome-back banner.

The streak itself is plain data from ProgressStore (streak_days,
record_play_today()'s PlayToday) -- this module only decides how to show
it. streak_tier()/welcome_message() are pure so the wording and tiers are
unit-testable without Flet; the build_* functions wrap them in controls.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import flet as ft

from app.progress.store import PlayToday
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import RADIUS_PILL, accent_gradient, lip_shadow, soft_shadow
from app.ui.color_utils import contrasting_text_color
from app.ui.theme_flet import ThemePreset, scaled


@dataclass(frozen=True)
class StreakTier:
    name: str
    emoji: str
    size_multiplier: float
    """How much bigger than the base chip text the flame renders."""
    label: str
    hot: bool
    """Whether the chip should pulse -- reserved for real streaks (3+ days)
    so a brand-new player's chip stays calm."""


def streak_tier(days: int) -> StreakTier:
    if days <= 0:
        return StreakTier("spark", "✨", 1.0, "Start a streak today!", hot=False)
    label = f"{days} day streak" if days == 1 else f"{days} day streak"
    if days < 3:
        return StreakTier("ember", "🔥", 1.0, label, hot=False)
    if days < 7:
        return StreakTier("flame", "🔥", 1.25, label, hot=True)
    if days < 30:
        return StreakTier("blaze", "🔥", 1.5, f"{label} — on fire!", hot=True)
    return StreakTier("inferno", "🔥", 1.8, f"{label} — legendary!", hot=True)


def welcome_message(name: str, play: Optional[PlayToday]) -> Optional[str]:
    """The one-line welcome-back moment for the Hub, or None when there is
    nothing to celebrate right now (not the first launch of the day, or no
    PlayToday recorded at all -- e.g. tests constructing AppState directly)."""
    if play is None or not play.first_play_today:
        return None
    if play.streak_continued and play.streak_days > 1:
        return f"🔥 Day {play.streak_days} streak, {name}! You came back — amazing!"
    if play.streak_reset:
        return f"🌱 Fresh start, {name}! A brand-new streak begins today."
    return f"👋 Welcome, {name}! Day 1 of your adventure begins now."


def build_streak_chip(theme: ThemePreset, days: int, scale: float, *, page=None) -> ft.Container:
    """The flame pill for a HUD strip. Pulses (bounded) when the streak is
    hot and a page is available to animate on."""
    fs = lambda base: scaled(base, scale)  # noqa: E731
    tier = streak_tier(days)
    accent = theme.warning if tier.hot else theme.card
    text_color = contrasting_text_color(accent) if tier.hot else theme.text
    chip = ft.Container(
        content=ft.Row(
            [
                ft.Text(tier.emoji, size=fs(round(16 * tier.size_multiplier))),
                ft.Text(tier.label, size=fs(14), weight=ft.FontWeight.BOLD, color=text_color),
            ],
            spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        gradient=accent_gradient(accent) if tier.hot else None,
        bgcolor=None if tier.hot else theme.card,
        border_radius=RADIUS_PILL,
        padding=ft.padding.Padding.symmetric(horizontal=14, vertical=8),
        shadow=lip_shadow(accent, depth=4) if tier.hot else soft_shadow(opacity=0.10, blur=10, dy=4),
        data={"kind": "streak_chip", "days": days, "tier": tier.name, "label": tier.label},
    )
    motion.prepare_pulse(chip)
    if tier.hot and page is not None:
        motion.pulse(page, chip, times=3, big=1.06)
    return chip


def build_welcome_banner(theme: ThemePreset, message: str, scale: float, *, page=None) -> ft.Container:
    """The celebratory welcome-back card -- pops in with an elastic scale
    when a page is available to animate on."""
    fs = lambda base: scaled(base, scale)  # noqa: E731
    banner = ft.Container(
        content=ft.Text(
            message, size=fs(16), weight=ft.FontWeight.BOLD,
            color=contrasting_text_color(theme.star), text_align=ft.TextAlign.CENTER,
        ),
        gradient=accent_gradient(theme.star), border_radius=20,
        padding=ft.padding.Padding.symmetric(horizontal=18, vertical=16),
        shadow=[lip_shadow(theme.star, depth=5), soft_shadow(theme.star, opacity=0.3)],
        alignment=ft.alignment.Alignment.CENTER,
        data={"kind": "welcome_banner", "message": message},
    )
    motion.prepare_pop(banner)
    motion.play_pop(page, banner)
    return banner
