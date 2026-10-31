"""Ambient life for the Flet game world: a living sky behind the hero
headers (time-of-day tint, drifting clouds, a sun or moon, twinkling
stars, rising XP sparkles) and per-World "weather" over the Adventure Map
roads (snow in Logic Peaks, leaves in Word Valley, glints in the Number
Kingdom, ...). Flet only, emoji only.

Everything is a positioned ft.Container in a Stack, animated with the
bounded loops in motion_flet (drift / twinkle / bob), so a view rebuilt on
the next route change can't leak a running task, and a page that can't
schedule (tests) gets the same scene standing still. Positions come from
a seeded RNG -- the moment name or the world id -- so a scene is stable
across rebuilds and unit-testable.

sky_moment() is the only clock in the module and takes the hour as a
parameter, so the Hub can be built at "night" in a test at noon.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import flet as ft

from app.ui.color_utils import with_alpha
from app.ui.components import motion_flet as motion
from app.ui.theme_flet import ThemePreset, scaled


# -- time of day ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SkyMoment:
    name: str
    tint: str
    tint_opacity: float
    """How strongly the tint washes over the header's sky gradient (0 = the
    plain theme sky)."""
    emoji: tuple[str, ...]
    """Decorations scattered across the sky, in the order they are placed."""
    greeting: str


SKY_MOMENTS: dict[str, SkyMoment] = {
    "dawn": SkyMoment("dawn", "#FFB36B", 0.30, ("🌅", "☁️", "🐦", "☁️"), "Good morning"),
    "day": SkyMoment("day", "#FFFFFF", 0.0, ("☀️", "☁️", "☁️", "🦋"), "Hello"),
    "dusk": SkyMoment("dusk", "#FF7E5F", 0.32, ("🌇", "☁️", "🦇", "☁️"), "Good evening"),
    "night": SkyMoment("night", "#1B2A6B", 0.48, ("🌙", "⭐", "✨", "⭐", "⭐"), "Up late"),
}


def sky_moment(hour: Optional[int] = None) -> SkyMoment:
    """Dawn 5-8, day 8-17, dusk 17-20, night otherwise -- from the local
    clock when `hour` is omitted."""
    if hour is None:
        hour = datetime.now().hour
    hour = hour % 24
    if 5 <= hour < 8:
        return SKY_MOMENTS["dawn"]
    if 8 <= hour < 17:
        return SKY_MOMENTS["day"]
    if 17 <= hour < 20:
        return SKY_MOMENTS["dusk"]
    return SKY_MOMENTS["night"]


# How each decoration moves once the page can animate. "rise" is the XP
# sparkle: it floats upward while glinting.
_SKY_MOTION: dict[str, str] = {
    "☁️": "drift", "🐦": "drift", "🦋": "drift", "🦇": "drift",
    "☀️": "bob", "🌙": "bob",
    "⭐": "twinkle", "💫": "twinkle",
    "✨": "rise",
}
SPARKLE_EMOJI = ("✨", "💫", "✨", "⭐")
SPARKLE_COUNT = 4


def _animate(page, particle: ft.Container, move: str) -> None:
    if move == "drift":
        motion.prepare_drift(particle, seconds=5.0)
        if page is not None:
            motion.drift(page, particle, times=3, dx=1.4, seconds=5.0)
    elif move == "fall":
        motion.prepare_drift(particle, seconds=3.5)
        if page is not None:
            motion.drift(page, particle, times=4, dx=0.3, dy=1.6, seconds=3.5)
    elif move == "bob":
        motion.prepare_bob(particle)
        if page is not None:
            motion.bob(page, particle, times=6, dy=0.12)
    elif move == "twinkle":
        motion.prepare_twinkle(particle)
        if page is not None:
            motion.twinkle(page, particle, times=5)
    elif move == "rise":
        motion.prepare_drift(particle, seconds=2.8)
        motion.prepare_twinkle(particle, seconds=1.4)
        if page is not None:
            motion.drift(page, particle, times=3, dx=0.2, dy=-1.8, seconds=2.8)
            motion.twinkle(page, particle, times=6, low=0.15, seconds=1.4)


def _particle(emoji: str, size: int, *, left: Optional[float], right: Optional[float], top: float, opacity: float, kind: str, extra: dict) -> ft.Container:
    return ft.Container(
        content=ft.Text(emoji, size=size),
        left=left, right=right, top=top, opacity=opacity,
        data={"kind": kind, "emoji": emoji, **extra},
    )


def build_sky_backdrop(
    theme: ThemePreset, *, moment: Optional[SkyMoment] = None, scale: float = 1.0,
    sparkles: bool = False, page=None, rng: Optional[random.Random] = None,
) -> ft.Stack:
    """The layer hero_header() paints behind its content: a time-of-day
    tint washing the sky gradient, the moment's decorations spread across
    the band (alternating left- and right-anchored so they cover a header
    of any width), and -- for the Hub -- XP sparkles rising from the
    bottom edge. Returns a positioned-fill Stack (left/top/right/bottom 0)."""
    moment = moment or sky_moment()
    chooser = rng if rng is not None else random.Random(moment.name)
    children: list[ft.Control] = []
    if moment.tint_opacity > 0:
        children.append(
            ft.Container(
                left=0, top=0, right=0, bottom=0,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.Alignment.TOP_CENTER, end=ft.alignment.Alignment.BOTTOM_CENTER,
                    colors=[with_alpha(moment.tint, moment.tint_opacity), with_alpha(moment.tint, 0.0)],
                ),
                data={"kind": "sky_tint", "moment": moment.name},
            )
        )
    for index, emoji in enumerate(moment.emoji):
        anchor = chooser.uniform(8, 120)
        size = scaled(chooser.choice((16, 20, 26)), scale)
        particle = _particle(
            emoji, size,
            left=anchor if index % 2 == 0 else None, right=anchor if index % 2 == 1 else None,
            top=chooser.uniform(6, 64), opacity=0.78,
            kind="sky_particle", extra={"moment": moment.name},
        )
        _animate(page, particle, _SKY_MOTION.get(emoji, "none"))
        children.append(particle)
    if sparkles:
        for index in range(SPARKLE_COUNT):
            anchor = chooser.uniform(20, 160)
            particle = _particle(
                SPARKLE_EMOJI[index % len(SPARKLE_EMOJI)], scaled(chooser.choice((14, 18)), scale),
                left=anchor if index % 2 == 0 else None, right=anchor if index % 2 == 1 else None,
                top=chooser.uniform(90, 150), opacity=0.7,
                kind="sky_sparkle", extra={},
            )
            _animate(page, particle, "rise")
            children.append(particle)
    return ft.Stack(
        children, left=0, top=0, right=0, bottom=0,
        data={"kind": "sky_backdrop", "moment": moment.name, "sparkles": sparkles},
    )


# -- per-World weather on the map ------------------------------------------------------------
WORLD_AMBIENCE: dict[str, tuple[str, ...]] = {
    "number_kingdom": ("💎", "✨", "👑", "💎", "✨"),
    "word_valley": ("🍃", "🦋", "🌸", "🍃", "🌸"),
    "logic_peaks": ("❄️", "❄️", "🌨️", "❄️", "❄️"),
    "arcade_islands": ("🌴", "🐚", "🌊", "🫧", "🫧"),
    "bug_swamp": ("🍄", "🐛", "💧", "🪲", "💧"),
    "scholar_tower": ("📚", "🕯️", "✒️", "📜", "🕯️"),
    "ai_observatory": ("🪐", "🛸", "🌟", "☄️", "🌟"),
}
DEFAULT_AMBIENCE: tuple[str, ...] = ("✨", "🍃", "⭐", "✨")

_WORLD_MOTION: dict[str, str] = {
    "❄️": "fall", "🌨️": "fall", "🌸": "fall", "💧": "fall", "☄️": "fall",
    "🍃": "drift", "🦋": "drift", "🌊": "drift", "🐛": "drift", "🪲": "drift", "🛸": "drift",
    "💎": "twinkle", "✨": "twinkle", "👑": "twinkle", "🕯️": "twinkle", "🌟": "twinkle", "⭐": "twinkle",
    "🫧": "rise",
    "🌴": "bob", "📜": "bob", "🪐": "bob",
}


def world_ambience_emoji(world_id: str) -> tuple[str, ...]:
    return WORLD_AMBIENCE.get(world_id, DEFAULT_AMBIENCE)


def build_world_ambience(
    world_id: str, width: float, height: float, *, scale: float = 1.0,
    page=None, count: Optional[int] = None, rng: Optional[random.Random] = None,
) -> list[ft.Container]:
    """Semi-transparent weather particles to slot into a world's road Stack
    between the road canvas and the nodes. Seeded by the world id so the
    scene is the same on every visit; `count` defaults to the world's
    whole emoji set, repeated if more are asked for."""
    emoji = world_ambience_emoji(world_id)
    total = count if count is not None else len(emoji)
    chooser = rng if rng is not None else random.Random(world_id)
    particles: list[ft.Container] = []
    for index in range(total):
        face = emoji[index % len(emoji)]
        particle = _particle(
            face, scaled(chooser.choice((16, 20, 24)), scale),
            left=chooser.uniform(6, max(6.0, width - 40)), right=None,
            top=chooser.uniform(8, max(8.0, height - 70)), opacity=0.55,
            kind="world_ambience", extra={"world": world_id},
        )
        _animate(page, particle, _WORLD_MOTION.get(face, "none"))
        particles.append(particle)
    return particles
