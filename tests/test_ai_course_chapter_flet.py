"""Exercises build_course_chapter_view() called for the "🤖 AI & Machine
Learning" course (course=AI_ML_COURSE) -- mirrors test_course_chapter_flet.py's
pattern, confirming gating/routing work the same for a second course, and
that its quiz items route to the /ai-course-quiz/ prefix instead of
/course-quiz/."""
from __future__ import annotations

import flet as ft
import pytest

from app.engine.categories import get_topic_icon
from app.engine.courses import AI_ML_COURSE
from app.ui.app_state_flet import AppState
from app.ui.course_chapter_flet import build_course_chapter_view

_CHAPTER = "ai_foundations"


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


def test_ai_foundations_renders_three_topic_headers_and_nine_items(state):
    page = FakePage()
    view = build_course_chapter_view(page, state, _CHAPTER, course=AI_ML_COURSE)
    rest = view.controls[2:]

    headers = [c for c in rest if isinstance(c, ft.Row)]
    items = [c for c in rest if isinstance(c, ft.Container)]
    expected_topics = ["What is AI?", "Rule-Based Decisions", "Types of AI"]
    assert [h.controls[0].value for h in headers] == [f"{get_topic_icon(t)} {t}" for t in expected_topics]
    assert len(items) == 9


def test_only_first_item_of_each_topic_unlocked_initially(state):
    page = FakePage()
    view = build_course_chapter_view(page, state, _CHAPTER, course=AI_ML_COURSE)
    items = [c for c in view.controls[2:] if isinstance(c, ft.Container)]

    # Indices 0-2 are "What is AI?"'s 3 items, 3-5 are "Rule-Based Decisions"',
    # 6-8 are "Types of AI"'s.
    assert items[0].content.controls[2].disabled is False
    assert items[1].content.controls[2].disabled is True
    assert items[2].content.controls[2].disabled is True
    assert items[3].content.controls[2].disabled is False  # second topic's first item, always open
    assert items[4].content.controls[2].disabled is True
    assert items[5].content.controls[2].disabled is True
    assert items[6].content.controls[2].disabled is False  # third topic's first item, always open
    assert items[7].content.controls[2].disabled is True
    assert items[8].content.controls[2].disabled is True


def test_non_quiz_item_navigates_to_the_shared_lesson_route(state):
    lessons = [l for l in state.lesson_engine.lessons_in_category(_CHAPTER) if l.topic == "What is AI?"]
    page = FakePage()
    view = build_course_chapter_view(page, state, _CHAPTER, course=AI_ML_COURSE)
    items = [c for c in view.controls[2:] if isinstance(c, ft.Container)]

    items[0].content.controls[2].on_click(None)
    assert page.routes_visited == [f"/lesson/{lessons[0].id}"]


def test_quiz_item_navigates_to_the_ai_course_quiz_route_once_unlocked(state):
    lessons = [l for l in state.lesson_engine.lessons_in_category(_CHAPTER) if l.topic == "What is AI?"]
    state.progress.complete_lesson(lessons[0].id, lessons[0].reward_stars)
    state.progress.complete_lesson(lessons[1].id, lessons[1].reward_stars)

    page = FakePage()
    view = build_course_chapter_view(page, state, _CHAPTER, course=AI_ML_COURSE)
    items = [c for c in view.controls[2:] if isinstance(c, ft.Container)]

    assert lessons[2].is_quiz is True
    items[2].content.controls[2].on_click(None)
    assert page.routes_visited == [f"/ai-course-quiz/{lessons[2].id}"]


def test_back_button_navigates_to_the_ai_course_map_route(state):
    page = FakePage()
    view = build_course_chapter_view(page, state, _CHAPTER, course=AI_ML_COURSE)
    header = view.controls[0]
    back_button = header.controls[0]

    back_button.on_click(None)
    assert page.routes_visited == ["/ai-course"]
