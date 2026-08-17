"""Exercises the phase-12 Adventure Map rewrite of the category browser:
a winding node path (one node per category) plus a separate, non-path
quiz tile -- built against a real AppState/LessonEngine, same pattern as
test_parent_dashboard_flet.py."""
from __future__ import annotations

import pytest

from app.engine.categories import get_category_meta
from app.ui.app_state_flet import AppState
from app.ui.category_map_flet import build_category_map_view


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
    # controls = [header, quiz_tile, Row([Stack])]
    return view.controls[2].controls[0]


def test_view_has_one_node_pair_per_category_plus_the_connector_layer(state):
    page = FakePage()
    view = build_category_map_view(page, state)
    categories = state.lesson_engine.categories()

    stack = _stack(view)
    # 1 connector container + (circle, caption) per category.
    assert len(stack.controls) == 1 + 2 * len(categories)


def test_quiz_tile_is_a_separate_card_not_a_path_node(state):
    page = FakePage()
    view = build_category_map_view(page, state)

    quiz_tile = view.controls[1]
    quiz_tile.on_click(None)
    assert page.routes_visited == ["/quiz"]


def test_first_category_node_navigates_to_its_levels_screen(state):
    page = FakePage()
    view = build_category_map_view(page, state)
    first_category = state.lesson_engine.categories()[0]

    stack = _stack(view)
    circle = stack.controls[1]  # index 0 is the connector container
    circle.on_click(None)
    assert page.routes_visited == [f"/categories/{first_category}"]


def test_node_icon_and_caption_match_the_category_meta(state):
    page = FakePage()
    view = build_category_map_view(page, state)
    first_category = state.lesson_engine.categories()[0]
    meta = get_category_meta(first_category)

    stack = _stack(view)
    circle, caption = stack.controls[1], stack.controls[2]
    assert circle.content.value == meta.icon
    assert circle.bgcolor == meta.color
    title_text, status_text = caption.content.controls
    assert title_text.value == meta.title
    assert "levels complete" in status_text.value


def test_caption_shows_all_complete_once_every_lesson_in_category_is_done(state):
    first_category = state.lesson_engine.categories()[0]
    lessons = state.lesson_engine.lessons_in_category(first_category)
    for lesson in lessons:
        state.progress.complete_lesson(lesson.id, 3)

    page = FakePage()
    view = build_category_map_view(page, state)
    stack = _stack(view)
    _circle, caption = stack.controls[1], stack.controls[2]
    _title_text, status_text = caption.content.controls
    assert status_text.value == "✅ All levels complete!"


def test_category_filter_restricts_node_count_to_the_filtered_categories(state):
    from app.engine.categories import PROJECT_CATEGORIES

    page = FakePage()
    view = build_category_map_view(page, state, category_filter=PROJECT_CATEGORIES)

    all_categories = state.lesson_engine.categories()
    expected = [c for c in all_categories if c in PROJECT_CATEGORIES]

    stack = _stack(view)
    assert len(stack.controls) == 1 + 2 * len(expected)


def test_category_filter_preserves_engine_categories_order(state):
    from app.engine.categories import PROJECT_CATEGORIES

    page = FakePage()
    view = build_category_map_view(page, state, category_filter=PROJECT_CATEGORIES)

    all_categories = state.lesson_engine.categories()
    expected_first = next(c for c in all_categories if c in PROJECT_CATEGORIES)
    expected_meta = get_category_meta(expected_first)

    stack = _stack(view)
    circle = stack.controls[1]
    assert circle.content.value == expected_meta.icon
    assert circle.bgcolor == expected_meta.color


def test_custom_heading_renders_in_place_of_default_title(state):
    page = FakePage()
    view = build_category_map_view(page, state, heading="🎯 Practise a Skill")

    header = view.controls[0]
    heading_text = header.controls[1]
    assert heading_text.value == "🎯 Practise a Skill"


def test_default_heading_unchanged_when_heading_not_passed(state):
    page = FakePage()
    view = build_category_map_view(page, state)

    header = view.controls[0]
    heading_text = header.controls[1]
    assert heading_text.value == "🗺️ Practice by Category"
