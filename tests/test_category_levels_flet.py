"""Exercises the Adventure Map level-selection screen: a winding road within
one category, lock/unlock/complete state still derived purely from
LessonEngine.is_unlocked() + the real progress store, plus the category
progress bar and Codey's marker over the next playable level."""
from __future__ import annotations

import pytest

from app.ui.adventure_map_layout import marker_position, zigzag_positions
from app.ui.app_state_flet import AppState
from app.ui.category_levels_flet import COMPLETED, LOCKED, UNLOCKED, build_category_levels_view, codey_levels_line
from tests.flet_testing import FakePage, all_of, one

CATEGORY = "code_crackers"


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def test_one_node_and_caption_per_lesson_plus_one_marker(state):
    lessons = state.lesson_engine.lessons_in_category(CATEGORY)
    view = build_category_levels_view(FakePage(), state, CATEGORY)
    assert len(all_of(view, "map_node")) == len(lessons)
    assert len(all_of(view, "map_caption")) == len(lessons)
    assert len(all_of(view, "you_are_here")) == 1


def test_first_level_starts_unlocked_and_shows_its_number(state):
    lessons = state.lesson_engine.lessons_in_category(CATEGORY)
    view = build_category_levels_view(FakePage(), state, CATEGORY)

    node = all_of(view, "map_node")[0]
    caption = all_of(view, "map_caption")[0]
    assert node.data["state"] == UNLOCKED
    assert node.data["label"] == str(lessons[0].category_level)
    assert node.on_click is not None
    assert caption.data["title"] == lessons[0].title
    assert caption.data["status"] == "🔓 Ready to play!"


def test_second_level_starts_locked(state):
    view = build_category_levels_view(FakePage(), state, CATEGORY)
    node = all_of(view, "map_node")[1]
    caption = all_of(view, "map_caption")[1]
    assert node.data["state"] == LOCKED
    assert node.data["label"] == "🔒"
    assert node.on_click is None
    assert caption.on_click is None
    assert caption.data["status"] == "🔒 Locked"


def test_completing_the_first_level_stars_it_unlocks_the_next_and_moves_the_marker(state):
    lessons = state.lesson_engine.lessons_in_category(CATEGORY)
    state.progress.complete_lesson(lessons[0].id, 3)

    view = build_category_levels_view(FakePage(), state, CATEGORY)
    nodes = all_of(view, "map_node")
    captions = all_of(view, "map_caption")
    assert nodes[0].data["state"] == COMPLETED
    assert nodes[0].data["stars"] == 3
    assert captions[0].data["status"] == "⭐⭐⭐"
    assert nodes[1].data["state"] == UNLOCKED
    assert nodes[1].on_click is not None

    positions = zigzag_positions(len(lessons))
    marker = one(view, "you_are_here")
    assert (marker.left, marker.top) == marker_position(positions[1])

    progress = one(view, "category_progress")
    assert (progress.data["done"], progress.data["total"]) == (1, len(lessons))
    assert one(progress, "power_bar").data["ratio"] == 1 / len(lessons)


def test_tapping_an_unlocked_node_or_its_caption_navigates_to_the_lesson(state):
    lessons = state.lesson_engine.lessons_in_category(CATEGORY)
    page = FakePage()
    view = build_category_levels_view(page, state, CATEGORY)

    all_of(view, "map_node")[0].on_click(None)
    all_of(view, "map_caption")[0].on_click(None)
    assert page.routes_visited == [f"/lesson/{lessons[0].id}"] * 2


def test_road_has_two_strokes_per_segment(state):
    lessons = state.lesson_engine.lessons_in_category(CATEGORY)
    view = build_category_levels_view(FakePage(), state, CATEGORY)
    canvas = one(view, "map_stack").controls[0].content
    assert len(canvas.shapes) == 2 * (len(lessons) - 1)


def test_header_uses_the_category_title(state):
    from app.engine.categories import get_category_meta

    meta = get_category_meta(CATEGORY)
    view = build_category_levels_view(FakePage(), state, CATEGORY)
    assert one(view, "hero_header").data["title"] == f"{meta.icon} {meta.title}"


def test_codey_levels_line():
    assert codey_levels_line("Numbers", 20, 20, None) == "Numbers conquered! Every level done ⭐"
    assert codey_levels_line("Numbers", 0, 20, "Counting") == "Up next: Counting. Let's go!"
    assert codey_levels_line("Numbers", 0, 0, None) == "Welcome to Numbers!"
