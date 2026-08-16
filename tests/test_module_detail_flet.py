"""Exercises the Python Journey per-module lesson list -- built against
a real AppState/LearningPathEngine, same pattern as
test_category_levels_flet.py."""
from __future__ import annotations

import pytest

from app.ui.app_state_flet import AppState
from app.ui.module_detail_flet import build_module_detail_view


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


def _stack(view):
    # controls = [header, description, Row([Stack])]
    return view.controls[2].controls[0]


def test_unknown_module_shows_a_friendly_message(state):
    page = FakePage()
    view = build_module_detail_view(page, state, "not-a-real-module")
    assert "Couldn't find module" in view.controls[0].value


def test_view_has_one_node_pair_per_lesson_in_the_module(state):
    page = FakePage()
    view = build_module_detail_view(page, state, "python-starter")
    lesson_ids = state.learning_path_engine.module_lesson_ids("python-starter")

    stack = _stack(view)
    assert len(stack.controls) == 1 + 2 * len(lesson_ids)


def test_first_lesson_is_unlocked_the_rest_are_locked(state):
    page = FakePage()
    view = build_module_detail_view(page, state, "python-starter")
    stack = _stack(view)

    first_circle = stack.controls[1]
    second_circle = stack.controls[3]
    assert first_circle.on_click is not None
    assert second_circle.on_click is None
    assert second_circle.content.value == "🔒"


def test_tapping_the_first_lesson_navigates_to_it(state):
    page = FakePage()
    view = build_module_detail_view(page, state, "python-starter")
    stack = _stack(view)

    stack.controls[1].on_click(None)
    assert page.routes_visited == ["/lesson/lesson_01"]


def test_completing_lessons_unlocks_the_next_one_in_the_module(state):
    state.progress.complete_lesson("lesson_01", 3)

    page = FakePage()
    view = build_module_detail_view(page, state, "python-starter")
    stack = _stack(view)

    first_circle = stack.controls[1]
    second_circle = stack.controls[3]
    assert first_circle.bgcolor == state.theme.success
    assert second_circle.on_click is not None


def test_checkpoint_lesson_shows_the_trophy_icon_when_unlocked(state):
    for lesson_id in ["lesson_01", "lesson_02", "lesson_03", "lesson_450"]:
        state.progress.complete_lesson(lesson_id, 3)

    page = FakePage()
    view = build_module_detail_view(page, state, "python-starter")
    stack = _stack(view)

    # 5 lessons in python-starter -> checkpoint is the 5th node: connector
    # (1) + 4 earlier (circle, caption) pairs (8) = index 9/10.
    checkpoint_circle = stack.controls[9]
    checkpoint_caption = stack.controls[10]
    assert checkpoint_circle.content.value == "🏆"
    _title_text, status_text = checkpoint_caption.content.controls
    assert status_text.value == "🏆 Checkpoint project!"
