"""Exercises the phase-12 Adventure Map rewrite of the level-selection
screen: a winding node path within one category, lock/unlock/complete
state still derived purely from LessonEngine.is_unlocked() + the real
progress store, same pattern as test_category_map_flet.py."""
from __future__ import annotations

import pytest

from app.ui.app_state_flet import AppState
from app.ui.category_levels_flet import build_category_levels_view


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
    # controls = [header, Row([Stack])]
    return view.controls[1].controls[0]


def _nodes(stack):
    """[(circle, caption), ...] -- stack.controls[0] is the connector layer."""
    body = stack.controls[1:]
    return list(zip(body[0::2], body[1::2]))


def test_view_has_one_node_pair_per_lesson_plus_the_connector_layer(state):
    category = "code_crackers"
    lessons = state.lesson_engine.lessons_in_category(category)
    page = FakePage()
    view = build_category_levels_view(page, state, category)

    stack = _stack(view)
    assert len(stack.controls) == 1 + 2 * len(lessons)


def test_first_level_starts_unlocked_and_shows_its_number(state):
    category = "code_crackers"
    lessons = state.lesson_engine.lessons_in_category(category)
    page = FakePage()
    view = build_category_levels_view(page, state, category)

    circle, caption = _nodes(_stack(view))[0]
    assert circle.content.value == str(lessons[0].category_level)
    assert circle.on_click is not None
    title_text, status_text = caption.content.controls
    assert title_text.value == lessons[0].title
    assert status_text.value == "🔓 Ready to play!"


def test_second_level_starts_locked(state):
    category = "code_crackers"
    page = FakePage()
    view = build_category_levels_view(page, state, category)

    circle, caption = _nodes(_stack(view))[1]
    assert circle.content.value == "🔒"
    assert circle.on_click is None
    _title_text, status_text = caption.content.controls
    assert status_text.value == "🔒 Locked"


def test_completing_the_first_level_unlocks_and_stars_it(state):
    category = "code_crackers"
    lessons = state.lesson_engine.lessons_in_category(category)
    state.progress.complete_lesson(lessons[0].id, 3)

    page = FakePage()
    view = build_category_levels_view(page, state, category)
    circle_0, caption_0 = _nodes(_stack(view))[0]
    circle_1, _caption_1 = _nodes(_stack(view))[1]

    _title_text, status_text = caption_0.content.controls
    assert status_text.value == "⭐⭐⭐"
    assert circle_1.content.value == str(lessons[1].category_level)  # now unlocked
    assert circle_1.on_click is not None


def test_tapping_an_unlocked_node_navigates_to_its_lesson(state):
    category = "code_crackers"
    lessons = state.lesson_engine.lessons_in_category(category)
    page = FakePage()
    view = build_category_levels_view(page, state, category)

    circle, _caption = _nodes(_stack(view))[0]
    circle.on_click(None)
    assert page.routes_visited == [f"/lesson/{lessons[0].id}"]


def test_tapping_the_caption_also_navigates_when_unlocked(state):
    category = "code_crackers"
    lessons = state.lesson_engine.lessons_in_category(category)
    page = FakePage()
    view = build_category_levels_view(page, state, category)

    _circle, caption = _nodes(_stack(view))[0]
    caption.on_click(None)
    assert page.routes_visited == [f"/lesson/{lessons[0].id}"]
