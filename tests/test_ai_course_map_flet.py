"""Exercises build_course_map_view() called for the "🤖 AI & Machine
Learning" course (course=AI_ML_COURSE) -- mirrors test_course_map_flet.py's
pattern, confirming the shared view-builder renders correctly for a second
course's own categories/route prefix, not just the default Python course."""
from __future__ import annotations

import pytest

from app.engine.categories import get_category_meta
from app.engine.course_status import compute_course_status
from app.engine.courses import AI_ML_COURSE
from app.ui.app_state_flet import AppState
from app.ui.course_map_flet import build_course_map_view


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


def _chapter_cards(view):
    return view.controls[4].controls


def test_one_card_per_chapter_in_curriculum_order(state):
    page = FakePage()
    view = build_course_map_view(page, state, course=AI_ML_COURSE)
    cards = _chapter_cards(view)

    assert len(cards) == len(AI_ML_COURSE.categories)
    titles = [card.content.controls[0].controls[1].value for card in cards]
    assert titles == [get_category_meta(c).title for c in AI_ML_COURSE.categories]


def test_ai_foundations_card_shows_0_of_6(state):
    page = FakePage()
    view = build_course_map_view(page, state, course=AI_ML_COURSE)
    card = next(
        c for c in _chapter_cards(view)
        if c.content.controls[0].controls[1].value == get_category_meta("ai_foundations").title
    )
    assert card.content.controls[1].value == "0/6 items"


def test_ai_tools_card_shows_0_of_6(state):
    page = FakePage()
    view = build_course_map_view(page, state, course=AI_ML_COURSE)
    card = next(
        c for c in _chapter_cards(view)
        if c.content.controls[0].controls[1].value == get_category_meta("ai_tools").title
    )
    assert card.content.controls[1].value == "0/6 items"


def test_chapter_card_click_navigates_to_the_ai_course_chapter_route(state):
    page = FakePage()
    view = build_course_map_view(page, state, course=AI_ML_COURSE)
    card = _chapter_cards(view)[0]

    button = card.content.controls[2]
    button.on_click(None)
    assert page.routes_visited == [f"/ai-course/{AI_ML_COURSE.categories[0]}"]


def test_hud_reflects_real_progress(state):
    first_chapter = AI_ML_COURSE.categories[0]
    lessons = state.lesson_engine.lessons_in_category(first_chapter)
    state.progress.complete_lesson(lessons[0].id, lessons[0].reward_stars)

    page = FakePage()
    view = build_course_map_view(page, state, course=AI_ML_COURSE)
    status = compute_course_status(state.lesson_engine, state.progress, AI_ML_COURSE.categories)

    hud = view.controls[2]
    lessons_text = hud.content.controls[1]
    assert lessons_text.value == f"{status.items_done}/{status.items_total} lessons complete"


def test_view_route_and_header_title_are_the_ai_course_s(state):
    page = FakePage()
    view = build_course_map_view(page, state, course=AI_ML_COURSE)
    assert view.route == "/ai-course"

    header = view.controls[0]
    assert header.controls[1].value == AI_ML_COURSE.title
