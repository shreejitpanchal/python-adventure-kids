"""Codey the Robot -- the app's companion mascot. Two forms:

- build_codey_avatar(): the small in-lesson reaction strip whose face and
  caption react to what just happened when the child runs their code
  (lesson_screen_flet.py).
- build_codey_companion(): the bigger Hub/Dashboard/Map presence -- a
  chunky face disc with a speech bubble carrying a context line ("Day 5
  streak! Ready for today's mission?"), an idle float (motion_flet.bob)
  and a cheer() for celebrations.

Emoji-only, no custom art assets, consistent with how the rest of the app
already communicates everything (rewards, errors, hints) through emoji +
short text rather than illustrations. Flet only, per the phase 7/8
CTk-parity decision.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable, Optional

import flet as ft

from app.ui.color_utils import with_alpha
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import accent_gradient, lip_shadow, soft_shadow
from app.ui.components.codey_face_flet import FaceHandle, blink_now, build_codey_face, expression_for_emoji, look
from app.ui.theme_flet import scaled


class CodeyState:
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    BLOCKED = "blocked"


# (face emoji, caption) per state. Kept short and encouraging, matching the
# tone of the rest of the app's output messages -- Codey reacts to the
# same result, it doesn't replace the existing friendly-error/output text.
_EXPRESSIONS: dict[str, tuple[str, str]] = {
    CodeyState.IDLE: ("🤖", "Ready when you are!"),
    CodeyState.RUNNING: ("💭", "Thinking..."),
    CodeyState.SUCCESS: ("🎉", "Awesome job!"),
    CodeyState.WARNING: ("🤔", "So close -- try again!"),
    CodeyState.ERROR: ("😵", "Uh oh, something broke!"),
    CodeyState.BLOCKED: ("🙅", "Can't do that one yet!"),
}


@dataclass
class CodeyHandle:
    control: ft.Control
    face_text: ft.Text
    caption_text: ft.Text
    set_state: Callable[[str], None]
    face_container: Optional[ft.Container] = None
    """The disc around the face -- what codey_performance_flet animates
    (bounce/spin/wobble) when Codey acts out a run's output."""
    face: Optional[FaceHandle] = None
    """The drawn face (codey_face_flet); face_text is now the semantic
    state (tests read it) and a small corner badge for non-robot emoji."""
    show_face: Optional[Callable[[str], None]] = None
    """show_face(emoji): set face_text and sync the drawn expression + badge."""


ROBOT_FACE = "🤖"


def _wire_drawn_face(face_text: ft.Text, face: FaceHandle) -> Callable[[str], None]:
    """face_text is the semantic face. The drawn face mirrors it through
    EMOJI_EXPRESSIONS; any emoji that isn't the plain robot also shows as
    the corner badge (face_text itself), so performances keep their flair."""

    def show_face(emoji: str) -> None:
        face_text.value = emoji
        face.set_expression(expression_for_emoji(emoji))
        face_text.visible = emoji != ROBOT_FACE

    return show_face


def build_codey_avatar(theme, scale: float = 1.0, *, page: Optional[object] = None) -> CodeyHandle:
    """The in-lesson reaction strip. With `page`, Codey also blinks and
    looks around while the child types (idle(), bounded)."""
    fs = lambda base: scaled(base, scale)  # noqa: E731
    idle_face, idle_caption = _EXPRESSIONS[CodeyState.IDLE]
    face_text = ft.Text(idle_face, size=fs(16), visible=False, right=-2, bottom=-2)
    caption_text = ft.Text(idle_caption, size=fs(12), color=theme.text_muted, italic=True)

    face = build_codey_face(theme, size=44)
    face_container = ft.Container(
        content=ft.Stack([face.control, face_text], width=44, height=44),
        bgcolor=theme.bg, border_radius=50, width=48, height=48,
        alignment=ft.alignment.Alignment.CENTER,
        offset=ft.Offset(0, 0), rotate=0.0, scale=1.0,
        animate_offset=ft.Animation(220, ft.AnimationCurve.EASE_IN_OUT),
        animate_rotation=ft.Animation(600, ft.AnimationCurve.EASE_IN_OUT),
        animate_scale=ft.Animation(220, ft.AnimationCurve.EASE_IN_OUT),
    )
    show_face = _wire_drawn_face(face_text, face)

    control = ft.Row(
        [
            face_container,
            ft.Column(
                [
                    ft.Text("Codey", size=fs(11), weight=ft.FontWeight.BOLD, color=theme.text_muted),
                    caption_text,
                ],
                spacing=0,
            ),
        ],
        spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def set_state(state: str) -> None:
        emoji, caption = _EXPRESSIONS.get(state, _EXPRESSIONS[CodeyState.IDLE])
        show_face(emoji)
        caption_text.value = caption

    if page is not None:
        idle(page, face_container, face)

    return CodeyHandle(
        control=control, face_text=face_text, caption_text=caption_text, set_state=set_state,
        face_container=face_container, face=face, show_face=show_face,
    )


# -- the companion (Hub / Dashboard / Map) -------------------------------------------
@dataclass
class CompanionHandle:
    control: ft.Control
    face_disc: ft.Control
    """The animated Stack (face disc + accessory badge)."""
    face_text: ft.Text
    line_text: ft.Text
    set_line: Callable[[str], None]
    cheer: Callable[[object], bool]
    """cheer(page): switch to the celebrating face + a quick pulse. Returns
    whether the pulse could be scheduled (see motion_flet.schedule)."""
    inner_disc: Optional[ft.Container] = None
    """The face disc itself (inside face_disc) -- what blinks and waves."""
    wave: Optional[Callable[[object], bool]] = None
    """wave(page): Codey's reaction to being tapped -- a wobble, a 👋 and
    a hello line that gives way to the original line a beat later."""
    face: Optional[FaceHandle] = None
    """The drawn face (codey_face_flet) inside the disc."""


# What Codey says when tapped, cycling so a second tap gets a new line.
WAVE_LINES: tuple[str, ...] = (
    "Hi! 👋 Ready to code?",
    "Beep boop! You found my ticklish spot 🤖",
    "Let's go earn some stars ⭐",
)
WAVE_FACE = "🤗"
# Idle loop timing: a blink every few seconds, a look-around on every
# other cycle. Bounded (IDLE_CYCLES) like every motion helper.
IDLE_CYCLES = 7
IDLE_GAPS: tuple[float, ...] = (3.0, 2.2, 3.6, 2.8, 3.2, 2.4, 3.4)
WAVE_LINE_SECONDS = 2.6


async def _idle(page, disc: ft.Container, face: Optional[FaceHandle] = None) -> None:
    for cycle in range(IDLE_CYCLES):
        await asyncio.sleep(IDLE_GAPS[cycle % len(IDLE_GAPS)])
        if face is not None:
            await blink_now(page, face)  # eyelids on the drawn face
        else:
            await motion._blink(page, disc)
        if cycle % 2 == 1:
            # Look around: a small tilt each way (and the pupils follow),
            # then straight ahead.
            for angle in (0.08, -0.08, 0.0):
                disc.rotate = angle
                if face is not None:
                    look(face, angle * 0.4)
                page.update()
                await asyncio.sleep(0.3)


def idle(page, disc: ft.Container, face: Optional[FaceHandle] = None) -> bool:
    """Codey's idle life: blinks, and now and then a look around."""
    return motion.schedule(page, _idle, page, disc, face)


async def _wave(page, show_face: Callable[[str], None], line_text: ft.Text, disc: ft.Container, previous_face: str, previous_line: str) -> None:
    await motion._wobble(page, disc, 6, 0.18)
    await asyncio.sleep(WAVE_LINE_SECONDS)
    show_face(previous_face)
    line_text.value = previous_line
    page.update()


def build_codey_companion(
    theme, scale: float, line: str, *, page: Optional[object] = None, face: str = "🤖",
    accessory: str = "",
) -> CompanionHandle:
    """Codey as a guide: big face disc on the left, speech bubble on the
    right. Pass `page` to start the idle float, blinks and look-arounds
    straight away (bounded -- see motion_flet) and to make the disc
    tappable (wave); without it (tests) the companion is static.
    `accessory` (see app/engine/titles.py's LevelTitle.codey_accessory) is
    worn as a small badge on the disc -- Codey "evolves" with the player's
    level."""
    fs = lambda base: scaled(base, scale)  # noqa: E731
    face_text = ft.Text(face, size=fs(18), text_align=ft.TextAlign.CENTER, right=-4, bottom=-4)
    accessory_text = ft.Text(accessory, size=fs(16), text_align=ft.TextAlign.CENTER)
    drawn_face = build_codey_face(theme, size=60)
    disc = ft.Container(
        content=ft.Stack([drawn_face.control, face_text], width=60, height=60),
        width=64, height=64, border_radius=32,
        gradient=accent_gradient(theme.primary),
        shadow=lip_shadow(theme.primary, depth=4),
        alignment=ft.alignment.Alignment.CENTER,
        rotate=0.0, animate_rotation=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
        data={"kind": "codey_disc"},
    )
    motion.prepare_blink(disc)
    show_face = _wire_drawn_face(face_text, drawn_face)
    show_face(face)
    accessory_badge = ft.Container(
        content=accessory_text, width=28, height=28, border_radius=14,
        bgcolor=theme.card, alignment=ft.alignment.Alignment.CENTER,
        shadow=soft_shadow(opacity=0.2, blur=6, dy=2),
        right=-4, top=-6, visible=bool(accessory),
        data={"kind": "codey_accessory", "accessory": accessory},
    )
    face_disc = ft.Stack([disc, accessory_badge], width=64, height=64)
    motion.prepare_bob(face_disc)
    wave_count = {"value": 0}

    line_text = ft.Text(line, size=fs(14), weight=ft.FontWeight.BOLD, color=theme.text)
    bubble = ft.Container(
        content=ft.Column(
            [ft.Text("Codey says", size=fs(10), color=theme.text_muted), line_text],
            spacing=2,
        ),
        bgcolor=with_alpha(theme.card, 0.92), border_radius=18,
        padding=ft.padding.Padding.symmetric(horizontal=14, vertical=10),
        shadow=soft_shadow(opacity=0.12, blur=12, dy=4),
        # expand=True bounds the bubble to the Row's remaining width so a
        # long line wraps instead of overflowing past the screen edge.
        expand=True,
    )
    control = ft.Row(
        [face_disc, bubble], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
        data={"kind": "codey_companion"},
    )

    def set_line(text: str) -> None:
        line_text.value = text

    def cheer(target_page) -> bool:
        show_face(_EXPRESSIONS[CodeyState.SUCCESS][0])
        motion.prepare_pulse(face_disc)
        return motion.pulse(target_page, face_disc, times=2, big=1.15)

    def wave(target_page) -> bool:
        """Tapped: a hug face, a wobble, and a hello that yields to the
        original line a beat later. The swap-back is scheduled, so a page
        that can't run tasks just keeps the hello (and stays consistent)."""
        previous_face, previous_line = face_text.value, line_text.value
        if previous_face == WAVE_FACE:
            return False  # mid-wave already; don't stack swap-backs
        show_face(WAVE_FACE)
        line_text.value = WAVE_LINES[wave_count["value"] % len(WAVE_LINES)]
        wave_count["value"] += 1
        motion.prepare_wobble(disc)
        scheduled = motion.schedule(target_page, _wave, target_page, show_face, line_text, disc, previous_face, previous_line)
        target_page.update()
        return scheduled

    if page is not None:
        motion.bob(page, face_disc)
        idle(page, disc, drawn_face)
        disc.on_click = lambda _e: wave(page)
        disc.ink = True

    return CompanionHandle(
        control=control, face_disc=face_disc, face_text=face_text, line_text=line_text,
        set_line=set_line, cheer=cheer, inner_disc=disc, wave=wave, face=drawn_face,
    )
