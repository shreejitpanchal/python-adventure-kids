"""Celebration effects for the Flet lesson screen's reward moment: an
emoji confetti burst and a level-up banner. Flet only.

Confetti is a Stack of small emoji particles parked at the center with
opacity 0; play_confetti() flips each one to a pre-chosen random
offset/rotation with opacity 1, then fades them out -- implicit
animations do the flight. Every particle's target is chosen at build
time from an injectable RNG, so tests can assert the burst without
Flet's event loop.
"""
from __future__ import annotations

import asyncio
import random
from typing import Optional

import flet as ft

from app.ui.color_utils import contrasting_text_color, with_alpha
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import accent_gradient, lip_shadow, soft_shadow
from app.ui.theme_flet import ThemePreset, scaled

CONFETTI_EMOJI = ("✨", "⭐", "🎉", "💫", "🌟", "🎊")
CONFETTI_COUNT = 16
CONFETTI_WIDTH = 300
CONFETTI_HEIGHT = 110
CONFETTI_FLIGHT_MS = 900
CONFETTI_FADE_MS = 500
# Flet offsets are fractions of the control's own size -- a 28px particle
# with offset x=6 travels ~170px. Spread wide, fly mostly upward.
_SPREAD_X = 6.0
_RISE_MIN, _RISE_MAX = -4.5, 0.8


def build_confetti(*, count: int = CONFETTI_COUNT, rng: Optional[random.Random] = None) -> ft.Stack:
    chooser = rng if rng is not None else random
    particles: list[ft.Container] = []
    for _ in range(count):
        target = ft.Offset(chooser.uniform(-_SPREAD_X, _SPREAD_X), chooser.uniform(_RISE_MIN, _RISE_MAX))
        spin = chooser.uniform(-3.0, 3.0)
        particle = ft.Container(
            content=ft.Text(chooser.choice(CONFETTI_EMOJI), size=chooser.choice((16, 20, 24))),
            left=CONFETTI_WIDTH / 2 - 14, top=CONFETTI_HEIGHT - 30,
            width=28, height=28,
            opacity=0.0, offset=ft.Offset(0, 0), rotate=0.0,
            animate_offset=ft.Animation(CONFETTI_FLIGHT_MS, ft.AnimationCurve.EASE_OUT),
            animate_opacity=ft.Animation(CONFETTI_FADE_MS, ft.AnimationCurve.EASE_IN),
            animate_rotation=ft.Animation(CONFETTI_FLIGHT_MS, ft.AnimationCurve.EASE_OUT),
            data={"kind": "confetti_particle", "target": (target.x, target.y), "spin": spin},
        )
        particles.append(particle)
    # Particles fly well past the Stack's own box; without clip_behavior
    # NONE, Flutter's Stack would clip them at its edge mid-flight.
    return ft.Stack(
        particles, width=CONFETTI_WIDTH, height=CONFETTI_HEIGHT,
        clip_behavior=ft.ClipBehavior.NONE,
        data={"kind": "confetti", "fired": False},
    )


def burst_now(confetti: ft.Stack) -> None:
    """Applies every particle's flight target immediately (no scheduling)."""
    for particle in confetti.controls:
        x, y = particle.data["target"]
        particle.offset = ft.Offset(x, y)
        particle.rotate = particle.data["spin"]
        particle.opacity = 1.0
    confetti.data = {**confetti.data, "fired": True}


def reset_confetti(confetti: ft.Stack) -> None:
    for particle in confetti.controls:
        particle.offset = ft.Offset(0, 0)
        particle.rotate = 0.0
        particle.opacity = 0.0
    confetti.data = {**confetti.data, "fired": False}


async def _fly_and_fade(page, confetti: ft.Stack) -> None:
    await asyncio.sleep(0.05)
    burst_now(confetti)
    page.update()
    await asyncio.sleep(CONFETTI_FLIGHT_MS / 1000)
    for particle in confetti.controls:
        particle.opacity = 0.0
    page.update()


def play_confetti(page, confetti: ft.Stack) -> bool:
    """Fires the burst on the page's event loop; when the page can't
    schedule tasks the particles are placed at their targets immediately so
    the celebration still shows (statically)."""
    reset_confetti(confetti)
    if not motion.schedule(page, _fly_and_fade, page, confetti):
        burst_now(confetti)
        return False
    return True


# -- star reveal ----------------------------------------------------------------------
STAR_FILLED = "⭐"
STAR_EMPTY = "☆"
STAR_REVEAL_GAP = 0.28


def build_star_row(theme: ThemePreset, max_stars: int, scale: float) -> ft.Container:
    """One slot per possible star, parked tiny and invisible; reveal_stars()
    pops the earned ones in one by one and jiggles the missing ones so the
    child sees what's left to earn."""
    slots: list[ft.Container] = []
    for _ in range(max_stars):
        slot = ft.Container(
            content=ft.Text(STAR_EMPTY, size=scaled(38, scale), color=theme.text_muted, text_align=ft.TextAlign.CENTER),
            width=52, height=52, alignment=ft.alignment.Alignment.CENTER,
            scale=0.2, opacity=0.0,
            animate_scale=ft.Animation(motion.POP_MS, ft.AnimationCurve.ELASTIC_OUT),
            animate_opacity=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        )
        motion.prepare_wobble(slot)
        slot.animate_scale = ft.Animation(motion.POP_MS, ft.AnimationCurve.ELASTIC_OUT)
        slots.append(slot)
    return ft.Container(
        content=ft.Row(slots, spacing=4, alignment=ft.MainAxisAlignment.CENTER),
        data={"kind": "star_row", "max": max_stars, "earned": None},
    )


def _star_slots(row: ft.Container) -> list[ft.Container]:
    return list(row.content.controls)


def set_stars(row: ft.Container, earned: int, theme: ThemePreset) -> None:
    for index, slot in enumerate(_star_slots(row)):
        filled = index < earned
        slot.content.value = STAR_FILLED if filled else STAR_EMPTY
        slot.content.color = None if filled else theme.text_muted
    row.data = {**row.data, "earned": earned}


def _show_all_stars(row: ft.Container) -> None:
    for slot in _star_slots(row):
        slot.scale = 1.0
        slot.opacity = 1.0


def reset_star_row(row: ft.Container) -> None:
    for slot in _star_slots(row):
        slot.scale = 0.2
        slot.opacity = 0.0
        slot.rotate = 0.0
    row.data = {**row.data, "earned": None}


async def _reveal_stars(page, row: ft.Container, earned: int) -> None:
    await asyncio.sleep(0.25)
    slots = _star_slots(row)
    for slot in slots:
        slot.scale = 1.0
        slot.opacity = 1.0
        page.update()
        await asyncio.sleep(STAR_REVEAL_GAP)
    for slot in slots[earned:]:
        await motion._wobble(page, slot, 4, 0.18)


def reveal_stars(page, row: ft.Container, earned: int, theme: ThemePreset) -> bool:
    set_stars(row, earned, theme)
    if not motion.schedule(page, _reveal_stars, page, row, earned):
        _show_all_stars(row)
        return False
    return True


# -- badge unlock moment ---------------------------------------------------------------
def show_badge_unlock(page, theme: ThemePreset, badge_id: str, scale: float) -> bool:
    """A modal 'NEW BADGE!' card: the badge spins in on a glowing disc with
    its title and description, dismissed by one big button. Returns False
    (and shows nothing) when the page has no dialog support -- the reward
    card's badge line still names the badge, so nothing is lost."""
    show_dialog = getattr(page, "show_dialog", None)
    if show_dialog is None:
        return False
    from app.engine.badges import get_badge_meta  # local import: keeps this module UI-only at import time
    from app.ui.components.adventure_kit_flet import emoji_badge

    fs = lambda base: scaled(base, scale)  # noqa: E731
    meta = get_badge_meta(badge_id)
    disc = emoji_badge(meta.icon, size=120, bgcolor=theme.star, scale=scale)
    disc.rotate = -0.8
    disc.scale = 0.3
    disc.animate_rotation = ft.Animation(700, ft.AnimationCurve.ELASTIC_OUT)
    disc.animate_scale = ft.Animation(700, ft.AnimationCurve.ELASTIC_OUT)
    halo = ft.Container(
        width=170, height=170, border_radius=85, bgcolor=with_alpha(theme.star, 0.35),
        animate_scale=ft.Animation(900, ft.AnimationCurve.EASE_IN_OUT), scale=0.8,
    )
    showcase = ft.Stack([halo, disc], width=170, height=170, alignment=ft.alignment.Alignment.CENTER)

    def close(_e=None) -> None:
        pop_dialog = getattr(page, "pop_dialog", None)
        if pop_dialog is not None:
            pop_dialog()

    dialog = ft.AlertDialog(
        modal=True,
        content=ft.Column(
            [
                ft.Text("🎖️ NEW BADGE!", size=fs(22), weight=ft.FontWeight.BOLD, color=theme.primary, text_align=ft.TextAlign.CENTER),
                showcase,
                ft.Text(meta.title, size=fs(20), weight=ft.FontWeight.BOLD, color=theme.text, text_align=ft.TextAlign.CENTER),
                ft.Text(meta.description, size=fs(14), color=theme.text_muted, text_align=ft.TextAlign.CENTER),
                ft.Text("Codey says: that one's going straight to the Trophy Room! 🏆", size=fs(13), italic=True, color=theme.text_muted, text_align=ft.TextAlign.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12, tight=True,
        ),
        actions=[ft.TextButton("Awesome! 🎉", on_click=close)],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        data={"kind": "badge_unlock", "badge_id": badge_id, "title": meta.title},
    )
    show_dialog(dialog)

    async def spin_in() -> None:
        await asyncio.sleep(0.08)
        disc.rotate = 0.0
        disc.scale = 1.0
        halo.scale = 1.1
        page.update()

    motion.schedule(page, spin_in)
    return True


def build_level_up_banner(theme: ThemePreset, scale: float) -> ft.Container:
    """Hidden until a lesson success crosses an XP level boundary; the
    lesson screen sets the level and shows it (see show_level_up)."""
    fs = lambda base: scaled(base, scale)  # noqa: E731
    text_color = contrasting_text_color(theme.warning)
    banner = ft.Container(
        content=ft.Column(
            [
                ft.Text("⬆️ LEVEL UP!", size=fs(22), weight=ft.FontWeight.BOLD, color=text_color, text_align=ft.TextAlign.CENTER),
                ft.Text("", size=fs(14), color=text_color, text_align=ft.TextAlign.CENTER),
            ],
            spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        gradient=accent_gradient(theme.warning), border_radius=20,
        padding=ft.padding.Padding.symmetric(horizontal=18, vertical=12),
        shadow=[lip_shadow(theme.warning, depth=5), soft_shadow(theme.warning, opacity=0.3)],
        visible=False,
        data={"kind": "level_up_banner", "level": None},
    )
    motion.prepare_pop(banner)
    return banner


def show_level_up(page, banner: ft.Container, level: int, title: Optional[str] = None) -> None:
    detail = f"You reached Level {level}!"
    if title:
        detail += f" You're now a {title}!"
    detail += " New skins may be waiting in Settings."
    banner.content.controls[1].value = detail
    banner.data = {**banner.data, "level": level, "title": title}
    banner.visible = True
    motion.play_pop(page, banner)


def hide_level_up(banner: ft.Container) -> None:
    banner.visible = False
    banner.scale = 0.6
    banner.data = {**banner.data, "level": None}
