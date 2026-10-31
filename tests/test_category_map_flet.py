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
        canvas = one(stack, "road").content
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


def test_world_garden_starts_as_a_seedling_and_grows(state):
    from app.engine.worlds import GARDEN_STAGES

    view = build_category_map_view(FakePage(), state)
    gardens = all_of(view, "world_garden")
    assert len(gardens) == len(all_of(view, "world_header"))
    assert all(g.data["stage"] == GARDEN_STAGES[0] for g in gardens)
    assert gardens[0].content.value == GARDEN_STAGES[0]

    _complete_category(state, state.lesson_engine.categories()[0])
    grown = all_of(build_category_map_view(FakePage(), state), "world_garden")[0]
    assert grown.data["stage"] != GARDEN_STAGES[0]


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


# -- the living map: weather per world, sky, bouncing marker, press feel --------------------
def test_each_world_road_carries_its_own_weather_behind_the_nodes(state):
    from app.ui.components.ambience_flet import world_ambience_emoji

    view = build_category_map_view(FakePage(), state)
    for stack in all_of(view, "map_stack"):
        particles = [c for c in stack.controls if isinstance(c.data, dict) and c.data.get("kind") == "world_ambience"]
        assert particles, "every road has weather"
        world_id = particles[0].data["world"]
        assert {p.data["emoji"] for p in particles} <= set(world_ambience_emoji(world_id))
        first_node = next(i for i, c in enumerate(stack.controls) if isinstance(c.data, dict) and c.data.get("kind") == "map_node")
        assert all(stack.controls.index(p) < first_node for p in particles), "weather sits under the nodes"
    worlds_seen = {all_of(stack, "world_ambience")[0].data["world"] for stack in all_of(view, "map_stack")}
    assert worlds_seen == {header.data["world"] for header in all_of(view, "world_header")}


def test_each_world_road_is_drawn_on_its_own_scenery_under_the_road(state):
    from app.ui.components.scenery_flet import scene_for_world

    view = build_category_map_view(FakePage(), state)
    for stack in all_of(view, "map_stack"):
        scenery = stack.controls[0]
        assert scenery.data["kind"] == "scenery"
        assert scenery.data["scene"] == scene_for_world(scenery.data["world"])
        assert scenery.content.shapes
        assert stack.controls[1].data == {"kind": "road"}
    assert view.bottom_appbar.data["active"] == "map"


def test_world_header_offers_the_boss_only_once_the_world_is_complete(state):
    from app.engine.boss import boss_badge_id
    from app.engine.worlds import world_for_category

    first_category = state.lesson_engine.categories()[0]
    world = world_for_category(first_category)

    locked = next(h for h in all_of(build_category_map_view(FakePage(), state), "world_header") if h.data["world"] == world.id)
    assert locked.data["boss"] == "locked" and all_of(locked, "game_button") == []
    assert len(all_of(locked, "boss_locked")) == 1

    for category in world.categories:
        _complete_category(state, category)
    page = FakePage()
    ready = next(h for h in all_of(build_category_map_view(page, state), "world_header") if h.data["world"] == world.id)
    assert ready.data["boss"] == "ready"
    (button,) = all_of(ready, "game_button")
    assert "Boss" in button.data["text"]
    gesture = next(c for c in ready.content.controls[-1].controls)
    gesture.on_tap(None)
    assert page.routes_visited == [f"/boss/{world.id}"]

    state.progress.award_badge(boss_badge_id(world))
    beaten = next(h for h in all_of(build_category_map_view(FakePage(), state), "world_header") if h.data["world"] == world.id)
    assert beaten.data["boss"] == "beaten" and len(all_of(beaten, "boss_chip")) == 1


def test_map_sky_is_pinned_by_hour(state):
    dusk = build_category_map_view(FakePage(), state, hour=18)
    backdrop = one(dusk, "sky_backdrop")
    assert backdrop.data["moment"] == "dusk" and backdrop.data["sparkles"] is False


def test_marker_bounces_higher_and_longer_than_an_idle_float(state):
    from app.ui.components import motion_flet as motion
    from app.ui.components.map_path_flet import MARKER_BOUNCE_DY, MARKER_BOUNCES

    page = FakePage()
    view = build_category_map_view(page, state)
    marker = one(view, "you_are_here")
    bounce = next(args for args, _k in page.scheduled(motion._bob) if args[1] is marker)
    assert bounce[2] == MARKER_BOUNCES and bounce[3] == MARKER_BOUNCE_DY
    assert MARKER_BOUNCES > 6 and MARKER_BOUNCE_DY > 0.15


def test_nodes_and_quiz_tile_squash_under_the_finger(state):
    from app.ui.components import motion_flet as motion

    page = FakePage()
    view = build_category_map_view(page, state)
    node = all_of(view, "map_node")[0]
    assert node.on_tap_down is not None
    node.on_tap_down(None)
    assert node.scale == motion.PRESS_SCALE
    assert len(page.scheduled(motion._spring_back)) == 1
    assert one(view, "quiz_tile").on_tap_down is not None
