"""Codey acts out what the child's program just did.

After a successful run the lesson screen shows the raw output, and a beat
later Codey "performs" it: his face changes to match the concept the
lesson teaches, his caption types out what Python said (typewriter style),
and his disc bounces (loops), spins (randomness) or wobbles (an error).
performance_for() is a pure mapping from (output, lesson) to that
performance so the wording is unit-testable; perform() schedules the
animation on the page (bounded, and a no-op without a schedulable page --
see motion_flet). The immediate SUCCESS/ERROR caption is set by the lesson
screen before perform() runs, so tests and a page without a loop still see
the plain reaction.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import flet as ft

from app.ui.components import motion_flet as motion
from app.ui.components.codey_avatar_flet import CodeyHandle

TYPEWRITER_STEP_SECONDS = 0.022
TYPEWRITER_CHARS_PER_STEP = 2
MAX_QUOTE_CHARS = 60

_LOOP_TAGS = {"loops", "for-loops", "while-loops", "iteration"}
_DECISION_TAGS = {"conditionals", "comparison", "booleans"}
_NUMBER_TAGS = {"variables", "numbers", "addition", "subtraction", "multiplication", "division", "expressions"}
_INPUT_TAGS = {"input"}
_RANDOM_TAGS = {"random", "games"}
_TEXT_TAGS = {"strings", "f-strings", "print", "basics"}


@dataclass(frozen=True)
class Performance:
    face: str
    line: str
    move: str
    """One of "none", "bounce", "spin", "wobble"."""


def _quote(text: str) -> str:
    text = text.strip()
    if len(text) > MAX_QUOTE_CHARS:
        text = text[: MAX_QUOTE_CHARS - 1] + "…"
    return f"“{text}”"


def performance_for(stdout: str, lesson) -> Performance:
    lines = [line for line in stdout.splitlines() if line.strip()]
    tags = set(getattr(lesson, "concept_tags", ()) or ()) | {getattr(lesson, "category", "")}
    if not lines:
        return Performance("🤐", "That ran quietly — nothing was printed!", "none")
    first = _quote(lines[0])
    if tags & _LOOP_TAGS and len(lines) > 1:
        return Performance("🔁", f"Whee! I said it {len(lines)} times — {first}", "bounce")
    if tags & _RANDOM_TAGS:
        return Performance("🎲", f"Lucky roll! Python said {first}", "spin")
    if tags & _DECISION_TAGS:
        return Performance("🚦", f"Decision made: {first}", "none")
    if tags & _INPUT_TAGS:
        return Performance("🙋", f"You typed it, Python heard it: {first}", "none")
    if tags & _NUMBER_TAGS:
        return Performance("📦", f"Stored, crunched, printed: {first}", "none")
    if tags & _TEXT_TAGS:
        return Performance("🗣️", f"Python says {first}", "bounce")
    return Performance("🗣️", f"Python says {first}", "none")


def error_performance() -> Performance:
    return Performance("😵‍💫", "Whoa, I got dizzy! Let's read the hint together.", "wobble")


def graphical_performance() -> Performance:
    return Performance("🎮", "Look at it go — your game is alive!", "bounce")


async def _perform(page, handle: CodeyHandle, performance: Performance, delay: float) -> None:
    await asyncio.sleep(delay)
    handle.face_text.value = performance.face
    line = performance.line
    for end in range(TYPEWRITER_CHARS_PER_STEP, len(line) + TYPEWRITER_CHARS_PER_STEP, TYPEWRITER_CHARS_PER_STEP):
        handle.caption_text.value = line[:end]
        page.update()
        await asyncio.sleep(TYPEWRITER_STEP_SECONDS)
    handle.caption_text.value = line
    page.update()

    disc = handle.face_container
    if disc is None:
        return
    if performance.move == "bounce":
        for _ in range(3):
            disc.offset = ft.Offset(0, -0.35)
            page.update()
            await asyncio.sleep(0.22)
            disc.offset = ft.Offset(0, 0)
            page.update()
            await asyncio.sleep(0.22)
    elif performance.move == "spin":
        disc.rotate = 6.283
        page.update()
        await asyncio.sleep(0.65)
        disc.rotate = 0.0
        page.update()
    elif performance.move == "wobble":
        await motion._wobble(page, disc, 6, 0.25)


def perform(handle: CodeyHandle, page, performance: Performance, *, delay: float = 0.45) -> bool:
    """Schedules the performance; False (nothing happens) when the page
    can't run tasks."""
    return motion.schedule(page, _perform, page, handle, performance, delay)
