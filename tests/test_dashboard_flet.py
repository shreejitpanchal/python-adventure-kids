"""Exercises build_dashboard_view()'s layout order and the completed-missions
sidebar's category-level consolidation -- with a real AppState/LessonEngine,
same pattern as test_parent_dashboard_flet.py."""
from __future__ import annotations

import pytest

from app.ui.app_state_flet import AppState
from app.ui.dashboard_flet import build_dashboard_view


class FakePage:
    def __init__(self) -> None:
        self.routes_visited: list[str] = []

    def update(self) -> None:
        pass

    def go(self, route: str) -> None:
        self.routes_visited.append(route)


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def test_quick_quiz_card_appears_before_completed_missions(state):
    page = FakePage()
    view = build_dashboard_view(page, state)

    # controls = [header, spacer, xp_hud, spacer, mission_card, spacer,
    #             quiz_card, spacer, missions_sidebar, spacer, footer_text]
    texts_in_order = []
    for control in view.controls:
        content = getattr(control, "content", None)
        if content is not None and hasattr(content, "controls"):
            for c in content.controls:
                if hasattr(c, "value") and c.value:
                    texts_in_order.append(c.value)

    quiz_index = next(i for i, t in enumerate(texts_in_order) if "Quick Quiz" in t)
    missions_index = next(i for i, t in enumerate(texts_in_order) if "Completed Missions" in t)
    assert quiz_index < missions_index


def test_missions_sidebar_shows_placeholder_with_no_completions(state):
    page = FakePage()
    view = build_dashboard_view(page, state)

    sidebar = view.controls[8]  # see index map in the test above
    texts = [c.value for c in sidebar.content.controls if hasattr(c, "value")]
    assert any("Finish your first mission" in t for t in texts)


def test_missions_sidebar_consolidates_by_category_not_per_lesson(state):
    basics_ids = [lesson.id for lesson in state.lesson_engine.lessons_in_category("basics")]
    numbers_lessons = state.lesson_engine.lessons_in_category("numbers")
    for lesson_id in basics_ids:
        state.progress.complete_lesson(lesson_id, 3)
    for lesson in numbers_lessons[:3]:
        state.progress.complete_lesson(lesson.id, 3)

    page = FakePage()
    view = build_dashboard_view(page, state)

    sidebar = view.controls[8]
    chip_row = sidebar.content.controls[1]
    # One chip per category with progress (basics, numbers) -- not one per lesson.
    assert len(chip_row.controls) == 2


def test_missions_sidebar_chip_shows_done_over_total_and_navigates_to_category(state):
    numbers_lessons = state.lesson_engine.lessons_in_category("numbers")
    for lesson in numbers_lessons[:3]:
        state.progress.complete_lesson(lesson.id, 3)

    page = FakePage()
    view = build_dashboard_view(page, state)

    sidebar = view.controls[8]
    chip_row = sidebar.content.controls[1]
    numbers_chip = chip_row.controls[0]
    status_text = numbers_chip.content.controls[1].value
    assert status_text == f"3/{len(numbers_lessons)} completed"

    numbers_chip.on_click(None)
    assert page.routes_visited == ["/categories/numbers"]


def test_missions_sidebar_chip_shows_all_complete_when_category_finished(state):
    basics_lessons = state.lesson_engine.lessons_in_category("basics")
    for lesson in basics_lessons:
        state.progress.complete_lesson(lesson.id, 3)

    page = FakePage()
    view = build_dashboard_view(page, state)

    sidebar = view.controls[8]
    chip_row = sidebar.content.controls[1]
    basics_chip = chip_row.controls[0]
    status_text = basics_chip.content.controls[1].value
    assert status_text == "✅ All levels complete!"
