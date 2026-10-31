"""codey_face_flet: the drawn Codey changes expression in place, blinks in
two frames, and maps the app's emoji faces onto expressions."""
from __future__ import annotations

import asyncio

import flet.canvas as cv

from app.ui.components import codey_face_flet as face_module
from app.ui.components.codey_face_flet import EXPRESSIONS, build_codey_face, expression_for_emoji, look
from app.ui.theme_flet import get_preset
from tests.flet_testing import FakePage

THEME = get_preset("sunny_light")


def test_builds_a_canvas_with_eyes_pupils_and_a_mouth():
    handle = build_codey_face(THEME, size=64)
    assert handle.control.data == {"kind": "codey_face", "expression": "idle"}
    assert isinstance(handle.canvas, cv.Canvas)
    assert handle.canvas.width == 64 and handle.canvas.height == 64
    assert all(shape in handle.canvas.shapes for shape in (*handle.eyes, *handle.pupils, handle.mouth))


def test_every_expression_is_distinct_and_unknown_falls_back_to_idle():
    handle = build_codey_face(THEME)
    seen = set()
    for name in EXPRESSIONS:
        handle.set_expression(name)
        assert handle.expression == name and handle.control.data["expression"] == name
        seen.add((len(handle.mouth.elements), handle.mouth.paint.style, round(handle.eyes[0].height, 2), round(handle.pupils[0].x, 2)))
    assert len(seen) == len(EXPRESSIONS), "each mood looks different"
    handle.set_expression("not-a-mood")
    assert handle.expression == "idle"


def test_emoji_faces_map_onto_expressions():
    assert expression_for_emoji("🤖") == "idle"
    assert expression_for_emoji("🎉") == "happy"
    assert expression_for_emoji("😵") == "dizzy"
    assert expression_for_emoji("💭") == "thinking"
    assert expression_for_emoji("🦄") == "idle", "unknown emoji keep the plain face"


def test_blink_shuts_the_eyes_then_restores_the_expression(monkeypatch):
    async def no_sleep(_s):
        return None

    monkeypatch.setattr(face_module.asyncio, "sleep", no_sleep)
    handle = build_codey_face(THEME, size=64, expression="happy")
    open_height = handle.eyes[0].height
    page = FakePage()
    asyncio.run(face_module.blink_now(page, handle))
    assert handle.eyes[0].height == open_height and handle.expression == "happy"
    assert page.update_count == 2


def test_look_moves_the_pupils_sideways_only():
    handle = build_codey_face(THEME, size=100)
    before = [(pupil.x, pupil.y) for pupil in handle.pupils]
    look(handle, 0.05)
    after = [(pupil.x, pupil.y) for pupil in handle.pupils]
    assert all(a[0] == b[0] + 5 and a[1] == b[1] for a, b in zip(after, before))
