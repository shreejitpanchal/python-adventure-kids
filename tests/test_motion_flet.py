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
