"""Exercises build_dashboard_view()'s sections and the completed-missions
sidebar's category-level consolidation -- with a real AppState/LessonEngine.
Controls are found by their data["kind"] role (tests/flet_testing.py)."""
from __future__ import annotations

import pytest

from app.ui.app_state_flet import AppState
from app.ui.components.adventure_kit_flet import power_bar_fill
from app.ui.dashboard_flet import build_dashboard_view, codey_mission_line
from tests.flet_testing import FakePage, NoTaskPage, all_of, one, texts


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def test_sections_appear_in_order_header_xp_mission_quiz_missions(state):
    view = build_dashboard_view(FakePage(), state)
    order = [
        view.controls.index(one(view, "hero_header")),
        view.controls.index(one(view, "xp_hud")),
        view.controls.index(one(view, "mission_card")),
        view.controls.index(one(view, "quiz_card")),
        view.controls.index(one(view, "missions_sidebar")),
    ]
    assert order == sorted(order)


def test_mission_card_targets_the_resolved_current_lesson(state):
    page = FakePage()
    view = build_dashboard_view(page, state)
    card = one(view, "mission_card")
    summary = state.progress.get_summary()
    expected = state.lesson_engine.resolve_current(state.progress.get_completed_lesson_ids(), summary.current_lesson_id)

    assert card.data["lesson_id"] == expected.id
    assert card.data["already_completed"] is False
    assert expected.title in texts(card)

    button = one(view, "game_button")
    assert button.data["text"] == "▶ CONTINUE"


def test_mission_card_moves_on_once_the_current_lesson_is_done(state):
    summary = state.progress.get_summary()
    current = state.lesson_engine.resolve_current([], summary.current_lesson_id)
    state.progress.complete_lesson(current.id, 3)
    state.progress.set_current_lesson(current.id)  # a stale pointer at the finished lesson

    view = build_dashboard_view(FakePage(), state)
    # resolve_current() never trusts a pointer at a completed lesson, so the
    # mission tile advances to the next incomplete one and still says CONTINUE.
    card = one(view, "mission_card")
    assert card.data["lesson_id"] != current.id
    assert card.data["already_completed"] is False
    assert one(view, "game_button").data["text"] == "▶ CONTINUE"


def test_xp_hud_power_bar_reflects_xp_and_animates_on_arrival(state):
    state.progress.add_xp(50)  # level 1 needs 100 XP -> half full
    page = FakePage()
    view = build_dashboard_view(page, state)

    hud = one(view, "xp_hud")
    assert hud.data["level"] == 1
    bar = one(hud, "power_bar")
    assert bar.data["ratio"] == 0.5
    # play_power_bar parked the fill at 0 and scheduled the grow.
    assert power_bar_fill(bar).width == 0
    assert any(handler.__name__ == "_grow_fill" for handler, _a, _k in page.run_task_calls)


def test_xp_hud_power_bar_keeps_its_real_width_when_the_page_cannot_animate(state):
    state.progress.add_xp(50)
    view = build_dashboard_view(NoTaskPage(), state)
    bar = one(one(view, "xp_hud"), "power_bar")
    assert power_bar_fill(bar).width == round(bar.data["width"] * 0.5)


def test_quick_quiz_card_navigates_to_the_quiz(state):
    page = FakePage()
    view = build_dashboard_view(page, state)
    one(view, "quiz_card").on_click(None)
    assert page.routes_visited == ["/quiz"]


def test_missions_sidebar_shows_placeholder_with_no_completions(state):
    view = build_dashboard_view(FakePage(), state)
    sidebar = one(view, "missions_sidebar")
    assert sidebar.data["started"] == 0
    assert any("Finish your first mission" in t for t in texts(sidebar))
    assert all_of(view, "category_chip") == []


def test_missions_sidebar_consolidates_by_category_not_per_lesson(state):
    basics_ids = [lesson.id for lesson in state.lesson_engine.lessons_in_category("basics")]
    numbers_lessons = state.lesson_engine.lessons_in_category("numbers")
    for lesson_id in basics_ids:
        state.progress.complete_lesson(lesson_id, 3)
    for lesson in numbers_lessons[:3]:
        state.progress.complete_lesson(lesson.id, 3)

    view = build_dashboard_view(FakePage(), state)
    chips = all_of(view, "category_chip")
    # One chip per category with progress (basics, numbers) -- not one per lesson.
    assert {chip.data["category"] for chip in chips} == {"basics", "numbers"}


def test_missions_sidebar_chip_shows_done_over_total_and_navigates_to_category(state):
    numbers_lessons = state.lesson_engine.lessons_in_category("numbers")
    for lesson in numbers_lessons[:3]:
        state.progress.complete_lesson(lesson.id, 3)

    page = FakePage()
    view = build_dashboard_view(page, state)
    numbers_chip = next(chip for chip in all_of(view, "category_chip") if chip.data["category"] == "numbers")
    assert numbers_chip.data["status"] == f"3/{len(numbers_lessons)} completed"
    assert numbers_chip.data["status"] in texts(numbers_chip)

    numbers_chip.on_click(None)
    assert page.routes_visited == ["/categories/numbers"]


def test_missions_sidebar_chip_shows_all_complete_when_category_finished(state):
    for lesson in state.lesson_engine.lessons_in_category("basics"):
        state.progress.complete_lesson(lesson.id, 3)

    view = build_dashboard_view(FakePage(), state)
    basics_chip = next(chip for chip in all_of(view, "category_chip") if chip.data["category"] == "basics")
    assert basics_chip.data["status"] == "✅ All levels complete!"


def test_codey_mission_line():
    assert codey_mission_line("Meet Python", False) == "Today's mission: Meet Python. You've got this!"
    assert "Mission complete" in codey_mission_line("Meet Python", True)
