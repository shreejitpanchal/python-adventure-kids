"""Motion helpers for the Flet game-world UI: staggered entrance reveals,
pulses, wobbles and bobs -- Flet only (CustomTkinter has no implicit
animation primitives, see game_button_flet.py).

Flet animations are *implicit*: set `animate_x` on a control once, then
every later change to property `x` tweens instead of jumping. So an
"animation" here is just a property flip scheduled slightly after the
control reaches the client. Two rules keep this safe:

- Every scheduled task is **bounded** -- a fixed number of pulses/bobs,
  never `while True` -- so a view rebuilt on the next route change
  (app_window_flet.py clears page.views every time) can't leak a looping
  task that keeps updating a control nobody sees.
- Every helper degrades gracefully when the page can't schedule tasks
  (tests use FakePage stubs; some have no run_task at all): entrance
  reveals then apply their final state immediately, so nothing is ever
  left invisible, and the other helpers simply do nothing.
"""
from __future__ import annotations

import asyncio
from typing import Iterable

import flet as ft

ENTRANCE_MS = 420
ENTRANCE_DY = 0.12
POP_MS = 550
PULSE_MS = 420
WOBBLE_MS = 90
BOB_MS = 600


def schedule(page, coro_fn, *args, **kwargs) -> bool:
    """page.run_task(...) if the page has one; False (and no-op) otherwise."""
    run_task = getattr(page, "run_task", None)
    if run_task is None:
        return False
    run_task(coro_fn, *args, **kwargs)
    return True


# -- entrance --------------------------------------------------------------------
def prepare_entrance(control, *, dy: float = ENTRANCE_DY) -> None:
    """Starts `control` invisible and slightly below its resting spot, with
    the tweens armed -- pair with play_entrance()."""
    control.opacity = 0.0
    control.offset = ft.Offset(0, dy)
    control.animate_opacity = ft.Animation(ENTRANCE_MS, ft.AnimationCurve.EASE_OUT)
    control.animate_offset = ft.Animation(ENTRANCE_MS, ft.AnimationCurve.EASE_OUT_BACK)


def reveal_now(controls: Iterable) -> None:
    for control in controls:
        control.opacity = 1.0
        control.offset = ft.Offset(0, 0)


async def _reveal_staggered(page, controls: list, stagger_seconds: float) -> None:
    # Let the route change that built these controls flush them to the
    # client first, otherwise the flip arrives before there's anything to
    # animate and the controls simply appear in place.
    await asyncio.sleep(0.05)
    for control in controls:
        control.opacity = 1.0
        control.offset = ft.Offset(0, 0)
        page.update()
        await asyncio.sleep(stagger_seconds)


def play_entrance(page, controls: Iterable, *, stagger_ms: int = 70) -> bool:
    """Reveals `controls` (prepared with prepare_entrance) one after another.
    Returns False -- after revealing everything immediately instead -- when
    the page can't schedule the animation."""
    controls = list(controls)
    if not schedule(page, _reveal_staggered, page, controls, stagger_ms / 1000):
        reveal_now(controls)
        return False
    return True


# -- pop in -----------------------------------------------------------------------
def prepare_pop(control, *, from_scale: float = 0.6) -> None:
    control.scale = from_scale
    control.animate_scale = ft.Animation(POP_MS, ft.AnimationCurve.ELASTIC_OUT)


async def _pop(page, control) -> None:
    await asyncio.sleep(0.08)
    control.scale = 1.0
    page.update()


def play_pop(page, control) -> bool:
    if not schedule(page, _pop, page, control):
        control.scale = 1.0
        return False
    return True


# -- pulse / wobble / bob (bounded loops) -------------------------------------------
def prepare_pulse(control) -> None:
    control.scale = 1.0
    control.animate_scale = ft.Animation(PULSE_MS, ft.AnimationCurve.EASE_IN_OUT)


async def _pulse(page, control, times: int, big: float) -> None:
    await asyncio.sleep(0.3)
    for _ in range(times):
        control.scale = big
        page.update()
        await asyncio.sleep(PULSE_MS / 1000)
        control.scale = 1.0
        page.update()
        await asyncio.sleep(PULSE_MS / 1000)


def pulse(page, control, *, times: int = 3, big: float = 1.08) -> bool:
    """A gentle breathe -- `times` scale-up/scale-down cycles, then rest."""
    return schedule(page, _pulse, page, control, times, big)


def prepare_wobble(control) -> None:
    control.rotate = 0.0
    control.animate_rotation = ft.Animation(WOBBLE_MS, ft.AnimationCurve.EASE_IN_OUT)


async def _wobble(page, control, times: int, angle: float) -> None:
    for i in range(times):
        control.rotate = angle if i % 2 == 0 else -angle
        page.update()
        await asyncio.sleep(WOBBLE_MS / 1000)
    control.rotate = 0.0
    page.update()


def wobble(page, control, *, times: int = 6, angle: float = 0.12) -> bool:
    """A quick side-to-side shake (radians), ending upright."""
    return schedule(page, _wobble, page, control, times, angle)


def prepare_bob(control) -> None:
    control.offset = ft.Offset(0, 0)
    control.animate_offset = ft.Animation(BOB_MS, ft.AnimationCurve.EASE_IN_OUT)


async def _bob(page, control, times: int, dy: float) -> None:
    await asyncio.sleep(0.4)
    for _ in range(times):
        control.offset = ft.Offset(0, -dy)
        page.update()
        await asyncio.sleep(BOB_MS / 1000)
        control.offset = ft.Offset(0, 0)
        page.update()
        await asyncio.sleep(BOB_MS / 1000)


def bob(page, control, *, times: int = 4, dy: float = 0.08) -> bool:
    """An idle up-and-down float, `times` cycles, then rest."""
    return schedule(page, _bob, page, control, times, dy)
