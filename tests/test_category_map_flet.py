"""Exercises the Adventure Map category browser: one chunky node per
category on a winding road, a separate quiz tile above the map, and Codey's
"you are here" marker over the next category to explore -- built against a
real AppState/LessonEngine. Controls are found by data["kind"]."""
from __future__ import annotations

import pytest

from app.engine.categories import PROJECT_CATEGORIES, get_category_meta
from app.engine.worlds import world_for_category, worlds_in_order
from app.ui.adventure_map_layout import marker_position, zigzag_positions
from app.ui.app_state_flet import AppState
from app.ui.category_map_flet import DEFAULT_HEADING, build_category_map_view, codey_map_line
from tests.flet_testing import FakePage, all_of, one


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def _complete_category(state, category: str) -> None:
    for lesson in state.lesson_engine.lessons_in_category(category):
        state.progress.complete_lesson(lesson.id, 3)


def test_one_node_and_caption_per_category_plus_one_marker(state):
    view = build_category_map_view(FakePage(), state)
    categories = state.lesson_engine.categories()

    assert len(all_of(view, "map_node")) == len(categories)
    assert len(all_of(view, "map_caption")) == len(categories)
    assert len(all_of(view, "you_are_here")) == 1


def test_each_world_road_has_two_strokes_per_segment(state):
    view = build_category_map_view(FakePage(), state)
    grouped = worlds_in_order(state.lesson_engine.categories())
    stacks = all_of(view, "map_stack")
    assert len(stacks) == len(grouped)
    for stack, (_world, world_categories) in zip(stacks, grouped):
        canvas = stack.controls[0].content
        assert len(canvas.shapes) == 2 * (len(world_categories) - 1)


def test_worlds_get_a_header_card_each_in_curriculum_order(state):
    view = build_category_map_view(FakePage(), state)
    categories = state.lesson_engine.categories()
    grouped = worlds_in_order(categories)
    headers = all_of(view, "world_header")
    assert [h.data["world"] for h in headers] == [world.id for world, _ in grouped]
    assert headers[0].data["world"] == world_for_category(categories[0]).id
    assert all(h.data["done"] == 0 and h.data["complete"] is False for h in headers)


def test_world_header_tracks_progress_within_that_world(state):
    categories = state.lesson_engine.categories()
    _complete_category(state, categories[0])
    view = build_category_map_view(FakePage(), state)
    first_header = all_of(view, "world_header")[0]
    assert first_header.data["done"] == len(state.lesson_engine.lessons_in_category(categories[0]))
    assert first_header.data["complete"] is False, "the first world has more categories than the first one"


def test_filtered_map_shows_only_the_worlds_of_the_filtered_categories(state):
    view = build_category_map_view(FakePage(), state, category_filter=PROJECT_CATEGORIES)
    headers = all_of(view, "world_header")
    assert [h.data["world"] for h in headers] == ["arcade_islands"]
    assert headers[0].data["total"] == sum(
        len(state.lesson_engine.lessons_in_category(c)) for c in PROJECT_CATEGORIES
    )


def test_wide_layout_uses_three_lanes_and_a_wider_road(state):
    page = FakePage()
    page.width = 1200
    view = build_category_map_view(page, state)
    stack = all_of(view, "map_stack")[0]
    assert stack.width == 620
    nodes = all_of(stack, "map_node")
    if len(nodes) >= 3:
        xs = [node.left for node in nodes[:3]]
        assert xs[0] < xs[1] < xs[2], "left, middle, right lanes"


def test_quiz_tile_is_a_separate_card_not_a_path_node(state):
    page = FakePage()
    view = build_category_map_view(page, state)
    one(view, "quiz_tile").on_click(None)
    assert page.routes_visited == ["/quiz"]


def test_first_category_node_navigates_to_its_levels_screen(state):
    page = FakePage()
    view = build_category_map_view(page, state)
    first_category = state.lesson_engine.categories()[0]

    all_of(view, "map_node")[0].on_click(None)
    assert page.routes_visited == [f"/categories/{first_category}"]


def test_caption_tap_also_navigates(state):
    page = FakePage()
    view = build_category_map_view(page, state)
    first_category = state.lesson_engine.categories()[0]
    all_of(view, "map_caption")[0].on_click(None)
    assert page.routes_visited == [f"/categories/{first_category}"]


def test_node_icon_color_and_caption_match_the_category_meta(state):
    view = build_category_map_view(FakePage(), state)
    first_category = state.lesson_engine.categories()[0]
    meta = get_category_meta(first_category)

    node = all_of(view, "map_node")[0]
    caption = all_of(view, "map_caption")[0]
    assert node.data["icon"] == meta.icon
    assert node.data["color"] == meta.color
    assert node.content.content.value == meta.icon  # the face text really shows the icon
    assert caption.data["title"] == meta.title
    assert "levels complete" in caption.data["status"]


def test_marker_starts_over_the_first_category_and_moves_once_it_is_complete(state):
    categories = state.lesson_engine.categories()
    positions = zigzag_positions(len(categories))

    marker = one(build_category_map_view(FakePage(), state), "you_are_here")
    assert (marker.left, marker.top) == marker_position(positions[0])

    _complete_category(state, categories[0])
    view = build_category_map_view(FakePage(), state)
    marker = one(view, "you_are_here")
    assert (marker.left, marker.top) == marker_position(positions[1])
    node, caption = all_of(view, "map_node")[0], all_of(view, "map_caption")[0]
    assert node.data["all_done"] is True
    assert caption.data["status"] == "✅ All levels complete!"


def test_category_filter_restricts_nodes_and_preserves_engine_order(state):
    view = build_category_map_view(FakePage(), state, category_filter=PROJECT_CATEGORIES)
    expected = [c for c in state.lesson_engine.categories() if c in PROJECT_CATEGORIES]
    nodes = all_of(view, "map_node")
    assert [node.data["category"] for node in nodes] == expected


def test_custom_heading_renders_in_place_of_default_title(state):
    view = build_category_map_view(FakePage(), state, heading="🎯 Practise a Skill")
    assert one(view, "hero_header").data["title"] == "🎯 Practise a Skill"


def test_default_heading_unchanged_when_heading_not_passed(state):
    view = build_category_map_view(FakePage(), state)
    assert one(view, "hero_header").data["title"] == DEFAULT_HEADING == "🗺️ Practice by Category"


def test_codey_map_line():
    assert codey_map_line("Numbers") == "Next stop: Numbers. Tap it to explore!"
    assert codey_map_line("Numbers", "Number Kingdom") == "Next stop: Numbers, in the Number Kingdom. Tap it to explore!"
    assert "Legendary" in codey_map_line(None)
