"""Codey drawn as vector art on a flet.canvas instead of the 🤖 emoji: a
rounded head with an antenna, two eyes whose pupils look around, eyelids
that blink, and a mouth that changes with his mood. The face is what the
companion disc and the in-lesson avatar show; the emoji faces the rest of
the app still sets (codey_avatar_flet._EXPRESSIONS, the performances) are
mapped onto an expression here and shown as a small corner badge for
variety, so nothing that set an emoji before has to change.

set_expression() mutates the shapes in place; the caller flushes with
page.update() like every other control change. blink_now() is an async
two-frame squeeze used by codey_avatar_flet's idle loop. Flet only.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Callable

import flet as ft
import flet.canvas as cv

from app.ui.color_utils import darken, lighten

EXPRESSIONS: tuple[str, ...] = ("idle", "happy", "thinking", "puzzled", "dizzy", "stop", "surprised", "sleepy")
BLINK_SECONDS = 0.11

# Emoji the rest of the app sets on face_text -> expression drawn here.
EMOJI_EXPRESSIONS: dict[str, str] = {
    "🤖": "idle",
    "💭": "thinking",
    "🎉": "happy",
    "🤗": "happy",
    "🤔": "puzzled",
    "😵": "dizzy",
    "😵‍💫": "dizzy",
    "🙅": "stop",
    "🔁": "happy",
    "🎲": "surprised",
    "🚦": "thinking",
    "🙋": "happy",
    "📦": "idle",
    "🗣️": "happy",
    "🤐": "sleepy",
    "🎮": "surprised",
}


def expression_for_emoji(emoji: str) -> str:
    return EMOJI_EXPRESSIONS.get(emoji, "idle")


@dataclass
class FaceHandle:
    control: ft.Container
    canvas: cv.Canvas
    size: float
    eyes: tuple[cv.Oval, cv.Oval]
    pupils: tuple[cv.Circle, cv.Circle]
    mouth: cv.Path
    expression: str
    set_expression: Callable[[str], None]


def _mouth_elements(size: float, expression: str) -> list:
    s = size
    left, right, y = s * 0.33, s * 0.67, s * 0.66
    mid = s * 0.5
    if expression in ("happy",):
        return [cv.Path.MoveTo(left, y), cv.Path.QuadraticTo(mid, y + s * 0.2, right, y), cv.Path.Close()]
    if expression == "idle":
        return [cv.Path.MoveTo(left, y), cv.Path.QuadraticTo(mid, y + s * 0.12, right, y)]
    if expression == "thinking":
        return [cv.Path.MoveTo(left + s * 0.04, y + s * 0.03), cv.Path.LineTo(right - s * 0.04, y + s * 0.03)]
    if expression == "puzzled":
        return [cv.Path.MoveTo(left, y + s * 0.04), cv.Path.QuadraticTo(s * 0.42, y - s * 0.06, mid, y + s * 0.02), cv.Path.QuadraticTo(s * 0.58, y + s * 0.1, right, y)]
    if expression == "dizzy":
        return [
            cv.Path.MoveTo(left, y), cv.Path.LineTo(s * 0.41, y + s * 0.06), cv.Path.LineTo(s * 0.5, y - s * 0.02),
            cv.Path.LineTo(s * 0.59, y + s * 0.06), cv.Path.LineTo(right, y),
        ]
    if expression == "stop":
        return [cv.Path.MoveTo(left, y + s * 0.08), cv.Path.QuadraticTo(mid, y - s * 0.08, right, y + s * 0.08)]
    if expression == "surprised":
        return [
            cv.Path.MoveTo(mid, y - s * 0.06), cv.Path.QuadraticTo(mid + s * 0.09, y - s * 0.06, mid + s * 0.09, y + s * 0.03),
            cv.Path.QuadraticTo(mid + s * 0.09, y + s * 0.12, mid, y + s * 0.12),
            cv.Path.QuadraticTo(mid - s * 0.09, y + s * 0.12, mid - s * 0.09, y + s * 0.03),
            cv.Path.QuadraticTo(mid - s * 0.09, y - s * 0.06, mid, y - s * 0.06), cv.Path.Close(),
        ]
    # sleepy
    return [cv.Path.MoveTo(left + s * 0.06, y + s * 0.02), cv.Path.QuadraticTo(mid, y + s * 0.06, right - s * 0.06, y + s * 0.02)]


# (pupil dx, pupil dy, eyelid openness 0..1) per expression, as fractions of size.
_EYES: dict[str, tuple[float, float, float]] = {
    "idle": (0.0, 0.0, 1.0),
    "happy": (0.0, -0.02, 0.85),
    "thinking": (0.035, -0.03, 0.8),
    "puzzled": (-0.03, 0.0, 0.75),
    "dizzy": (0.0, 0.02, 1.0),
    "stop": (0.0, 0.0, 0.6),
    "surprised": (0.0, -0.01, 1.0),
    "sleepy": (0.0, 0.03, 0.3),
}

EYE_W, EYE_H = 0.2, 0.24
EYE_LX, EYE_RX, EYE_Y = 0.3, 0.7, 0.42


def build_codey_face(theme, *, size: float = 64, expression: str = "idle", color: str | None = None) -> FaceHandle:
    """A drawn Codey `size` px square. `color` is the head color (defaults
    to the theme primary -- the companion disc's own gradient shows through
    the transparent background around the head)."""
    s = float(size)
    head_color = color or theme.primary
    face_color = lighten(head_color, 0.35)
    dark = darken(head_color, 0.55)

    antenna = cv.Line(s * 0.5, s * 0.16, s * 0.5, s * 0.06, paint=ft.Paint(color=dark, stroke_width=max(2.0, s * 0.045), style=ft.PaintingStyle.STROKE))
    antenna_tip = cv.Circle(s * 0.5, s * 0.06, s * 0.05, paint=ft.Paint(color=theme.star, style=ft.PaintingStyle.FILL))
    head = cv.Rect(s * 0.14, s * 0.16, s * 0.72, s * 0.72, border_radius=s * 0.22, paint=ft.Paint(color=head_color, style=ft.PaintingStyle.FILL))
    visor = cv.Rect(s * 0.2, s * 0.28, s * 0.6, s * 0.5, border_radius=s * 0.16, paint=ft.Paint(color=face_color, style=ft.PaintingStyle.FILL))
    ears = [
        cv.Rect(s * 0.06, s * 0.42, s * 0.08, s * 0.2, border_radius=s * 0.03, paint=ft.Paint(color=dark, style=ft.PaintingStyle.FILL)),
        cv.Rect(s * 0.86, s * 0.42, s * 0.08, s * 0.2, border_radius=s * 0.03, paint=ft.Paint(color=dark, style=ft.PaintingStyle.FILL)),
    ]
    white = ft.Paint(color="#FFFFFF", style=ft.PaintingStyle.FILL)
    eye_l = cv.Oval(s * (EYE_LX - EYE_W / 2), s * (EYE_Y - EYE_H / 2), s * EYE_W, s * EYE_H, paint=white)
    eye_r = cv.Oval(s * (EYE_RX - EYE_W / 2), s * (EYE_Y - EYE_H / 2), s * EYE_W, s * EYE_H, paint=white)
    pupil_paint = ft.Paint(color=dark, style=ft.PaintingStyle.FILL)
    pupil_l = cv.Circle(s * EYE_LX, s * EYE_Y, s * 0.055, paint=pupil_paint)
    pupil_r = cv.Circle(s * EYE_RX, s * EYE_Y, s * 0.055, paint=pupil_paint)
    mouth = cv.Path(_mouth_elements(s, expression), paint=ft.Paint(color=dark, stroke_width=max(2.0, s * 0.045), style=ft.PaintingStyle.STROKE, stroke_cap=ft.StrokeCap.ROUND))

    canvas = cv.Canvas(shapes=[antenna, antenna_tip, head, visor, *ears, eye_l, eye_r, pupil_l, pupil_r, mouth], width=s, height=s)
    control = ft.Container(content=canvas, width=s, height=s, data={"kind": "codey_face", "expression": expression})
    handle = FaceHandle(
        control=control, canvas=canvas, size=s, eyes=(eye_l, eye_r), pupils=(pupil_l, pupil_r),
        mouth=mouth, expression=expression, set_expression=lambda name: None,
    )

    def apply_eyes(openness: float, dx: float, dy: float) -> None:
        eye_h = s * EYE_H * max(0.08, openness)
        for eye, cx in ((eye_l, EYE_LX), (eye_r, EYE_RX)):
            eye.y = s * EYE_Y - eye_h / 2
            eye.height = eye_h
        for pupil, cx in ((pupil_l, EYE_LX), (pupil_r, EYE_RX)):
            pupil.x = s * (cx + dx)
            pupil.y = s * (EYE_Y + dy)

    def set_expression(name: str) -> None:
        if name not in _EYES:
            name = "idle"
        dx, dy, openness = _EYES[name]
        apply_eyes(openness, dx, dy)
        mouth.elements = _mouth_elements(s, name)
        mouth.paint.style = ft.PaintingStyle.FILL if name in ("happy", "surprised") else ft.PaintingStyle.STROKE
        handle.expression = name
        control.data = {"kind": "codey_face", "expression": name}

    handle.set_expression = set_expression
    set_expression(expression)
    return handle


async def blink_now(page, handle: FaceHandle) -> None:
    """Two frames: eyelids shut, then back to the expression's openness."""
    dx, dy, openness = _EYES.get(handle.expression, _EYES["idle"])
    s = handle.size
    for eye in handle.eyes:
        eye.y = s * EYE_Y - s * EYE_H * 0.04
        eye.height = s * EYE_H * 0.08
    page.update()
    await asyncio.sleep(BLINK_SECONDS)
    handle.set_expression(handle.expression)
    page.update()


def look(handle: FaceHandle, dx: float) -> None:
    """Shift the pupils sideways (fraction of size) without changing the
    expression -- the idle look-around."""
    _dx, dy, _openness = _EYES.get(handle.expression, _EYES["idle"])
    s = handle.size
    for pupil, cx in zip(handle.pupils, (EYE_LX, EYE_RX)):
        pupil.x = s * (cx + dx)
        pupil.y = s * (EYE_Y + dy)
