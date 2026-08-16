"""Exercises the Python Journey course map -- built against a real
AppState/LearningPathEngine, same FakePage pattern as
test_category_map_flet.py."""
from __future__ import annotations

import pytest

from app.ui.app_state_flet import AppState
from app.ui.journey_map_flet import build_journey_map_view


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
    # controls = [header, progress_text, Row([Stack])]
    return view.controls[2].controls[0]


def test_view_has_one_node_pair_per_module_plus_the_connector_layer(state):
    page = FakePage()
    view = build_journey_map_view(page, state)
    modules = state.learning_path_engine.modules()

    stack = _stack(view)
    assert len(stack.controls) == 1 + 2 * len(modules)


def test_progress_text_shows_module_1_of_8_with_no_progress(state):
    page = FakePage()
    view = build_journey_map_view(page, state)
    assert "Module 1 of 8" in view.controls[1].value


def test_first_module_node_is_unlocked_and_navigates(state):
    page = FakePage()
    view = build_journey_map_view(page, state)
    stack = _stack(view)
    circle = stack.controls[1]  # index 0 is the connector container

    assert circle.on_click is not None
    circle.on_click(None)
    assert page.routes_visited == ["/journey/python-starter"]


def test_second_module_node_is_locked(state):
    page = FakePage()
    view = build_journey_map_view(page, state)
    stack = _stack(view)
    # module 1 -> (circle, caption) at [1,2]; module 2 -> [3,4]
    circle_2, caption_2 = stack.controls[3], stack.controls[4]

    assert circle_2.on_click is None
    assert circle_2.content.value == "🔒"
    title_text, status_text = caption_2.content.controls
    assert status_text.value == "🔒 Locked"


def test_completing_module_1_unlocks_module_2_and_awards_the_badge_on_load(state):
    for lesson_id in ["lesson_01", "lesson_02", "lesson_03", "lesson_450", "lesson_451"]:
        state.progress.complete_lesson(lesson_id, 3)

    assert "module_python_starter" not in state.progress.get_badge_ids()

    page = FakePage()
    view = build_journey_map_view(page, state)

    # The catch-up check runs on load.
    assert "module_python_starter" in state.progress.get_badge_ids()

    stack = _stack(view)
    circle_1 = stack.controls[1]
    circle_2 = stack.controls[3]
    assert circle_1.bgcolor == state.theme.success  # completed
    assert circle_2.on_click is not None  # module 2 now unlocked

    assert "Module 2 of 8" in view.controls[1].value
