"""Motion helpers (app/ui/components/motion_flet.py): every helper must be
bounded, degrade without a schedulable page, and leave controls in a
sensible final state."""
from __future__ import annotations

import asyncio

import flet as ft

from app.ui.components import motion_flet as motion
from tests.flet_testing import FakePage, NoTaskPage


def _box() -> ft.Container:
    return ft.Container(width=10, height=10)


def test_schedule_returns_false_without_run_task_and_records_with_it():
    assert motion.schedule(NoTaskPage(), motion._pop, None, None) is False
    page = FakePage()
    assert motion.schedule(page, motion._pop, page, "ctl") is True
    assert page.scheduled(motion._pop) == [((page, "ctl"), {})]


def test_prepare_entrance_hides_and_arms_the_tweens():
    box = _box()
    motion.prepare_entrance(box)
    assert box.opacity == 0.0
    assert box.offset.y == motion.ENTRANCE_DY
    assert box.animate_opacity is not None and box.animate_offset is not None


def test_play_entrance_reveals_immediately_when_the_page_cannot_animate():
    boxes = [_box(), _box()]
    for box in boxes:
        motion.prepare_entrance(box)
    assert motion.play_entrance(NoTaskPage(), boxes) is False
    assert all(box.opacity == 1.0 and box.offset.y == 0 for box in boxes)


def test_play_entrance_schedules_one_staggered_reveal_that_updates_per_control():
    page = FakePage()
    boxes = [_box(), _box(), _box()]
    for box in boxes:
        motion.prepare_entrance(box)
    assert motion.play_entrance(page, boxes, stagger_ms=0) is True
    assert all(box.opacity == 0.0 for box in boxes), "nothing revealed until the task runs"

    ((handler, args, kwargs),) = page.run_task_calls
    asyncio.run(handler(*args, **kwargs))
    assert all(box.opacity == 1.0 and box.offset.y == 0 for box in boxes)
    assert page.update_count == len(boxes)


def test_play_pop_sets_final_scale_immediately_without_a_page():
    box = _box()
    motion.prepare_pop(box)
    assert box.scale == 0.6
    assert motion.play_pop(NoTaskPage(), box) is False
    assert box.scale == 1.0


def test_pulse_wobble_and_bob_are_bounded_and_end_at_rest():
    page = FakePage()
    box = _box()
    motion.prepare_pulse(box)
    motion.prepare_wobble(box)
    motion.prepare_bob(box)
    assert motion.pulse(page, box, times=1) and motion.wobble(page, box, times=2) and motion.bob(page, box, times=1)
    assert len(page.run_task_calls) == 3

    # Run the wobble for real (short): it must return to upright.
    wobble_call = page.scheduled(motion._wobble)[0]
    asyncio.run(motion._wobble(*wobble_call[0]))
    assert box.rotate == 0.0
    assert page.update_count == 3  # two tilts + the final reset


def test_pulse_and_bob_return_false_without_a_page():
    box = _box()
    assert motion.pulse(NoTaskPage(), box) is False
    assert motion.bob(NoTaskPage(), box) is False
    assert motion.wobble(NoTaskPage(), box) is False


# -- ambient loops --------------------------------------------------------------------
def test_drift_and_twinkle_are_bounded_and_return_to_rest(monkeypatch):
    monkeypatch.setattr(motion.asyncio, "sleep", _no_sleep)
    page = FakePage()
    box = _box()
    motion.prepare_drift(box, seconds=2.0)
    assert box.animate_offset.duration == 2000
    assert motion.drift(page, box, times=2, dx=1.0, dy=-0.5, seconds=2.0) is True
    ((args, _k),) = page.scheduled(motion._drift)
    asyncio.run(motion._drift(*args))
    assert box.offset.x == 0 and box.offset.y == 0
    assert page.update_count == 4  # out and back, twice

    star = _box()
    motion.prepare_twinkle(star)
    assert motion.twinkle(page, star, times=1, low=0.2) is True
    ((args, _k),) = page.scheduled(motion._twinkle)
    asyncio.run(motion._twinkle(*args))
    assert star.opacity == 1.0

    assert motion.drift(NoTaskPage(), box) is False
    assert motion.twinkle(NoTaskPage(), star) is False


def test_rattle_wobbles_in_bursts_and_ends_upright(monkeypatch):
    monkeypatch.setattr(motion.asyncio, "sleep", _no_sleep)
    page = FakePage()
    chest = _box()
    motion.prepare_wobble(chest)
    assert motion.rattle(page, chest, bursts=2, gap=0.0) is True
    ((args, _k),) = page.scheduled(motion._rattle)
    asyncio.run(motion._rattle(*args))
    assert chest.rotate == 0.0
    assert page.update_count == 2 * 7  # six tilts + reset, per burst
    assert motion.rattle(NoTaskPage(), chest) is False


def test_blink_squeezes_vertically_then_restores(monkeypatch):
    monkeypatch.setattr(motion.asyncio, "sleep", _no_sleep)
    page = FakePage()
    face = _box()
    motion.prepare_blink(face)
    assert face.scale.scale_y == 1.0
    assert motion.blink(page, face) is True
    ((args, _k),) = page.scheduled(motion._blink)
    asyncio.run(motion._blink(*args))
    assert face.scale.scale_y == 1.0 and face.scale.scale_x == 1.0
    assert page.update_count == 2
    assert motion.blink(NoTaskPage(), face) is False


# -- press / flash / float-up -----------------------------------------------------------
def test_press_squashes_now_and_springs_back_later(monkeypatch):
    monkeypatch.setattr(motion.asyncio, "sleep", _no_sleep)
    page = FakePage()
    card = _box()
    motion.prepare_press(card)
    assert card.scale == 1.0 and card.animate_scale.duration == motion.PRESS_MS
    assert motion.press(page, card) is True
    assert card.scale == motion.PRESS_SCALE and page.update_count == 1
    ((args, _k),) = page.scheduled(motion._spring_back)
    asyncio.run(motion._spring_back(*args))
    assert card.scale == 1.0


def test_press_never_leaves_a_control_squashed_when_it_cannot_spring_back():
    card = _box()
    motion.prepare_press(card)
    assert motion.press(NoTaskPage(), card) is False
    assert card.scale == 1.0


def test_prepare_press_keeps_an_existing_scale_animation():
    capsule = _box()
    motion.prepare_pulse(capsule)
    motion.prepare_press(capsule)
    assert capsule.animate_scale.duration == motion.PULSE_MS


def test_flash_shows_fades_and_hides_again(monkeypatch):
    monkeypatch.setattr(motion.asyncio, "sleep", _no_sleep)
    page = FakePage()
    wash = _box()
    motion.prepare_flash(wash)
    assert wash.visible is False and wash.opacity == 0.0
    assert motion.flash(page, wash, peak=0.5) is True
    ((args, _k),) = page.scheduled(motion._flash)
    asyncio.run(motion._flash(*args))
    assert wash.visible is False and wash.opacity == 0.0
    assert page.update_count == 3
    assert motion.flash(NoTaskPage(), wash) is False and wash.visible is False


def test_float_up_rises_fades_and_parks_back(monkeypatch):
    monkeypatch.setattr(motion.asyncio, "sleep", _no_sleep)
    page = FakePage()
    toast = _box()
    motion.prepare_float_up(toast)
    assert toast.opacity == 0.0
    assert motion.float_up(page, toast, dy=2.0) is True
    ((args, _k),) = page.scheduled(motion._float_up)
    asyncio.run(motion._float_up(*args))
    assert toast.opacity == 0.0 and toast.offset.y == 0
    assert page.update_count == 4
    assert motion.float_up(NoTaskPage(), toast) is False


async def _no_sleep(_seconds: float) -> None:
    """Stands in for asyncio.sleep so the bounded loops run instantly."""
    return None
