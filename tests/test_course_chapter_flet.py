"""Exercises build_course_chapter_view()'s 3-item list -- gating, status
text, and quiz-vs-lesson routing -- against a real AppState/LessonEngine,
same pattern as test_category_map_flet.py."""
from __future__ import annotations

import pytest

from app.engine.categories import COURSE_CATEGORIES
from app.ui.app_state_flet import AppState
from app.ui.course_chapter_flet import build_course_chapter_view

_CHAPTER = COURSE_CATEGORIES[0]


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


def _item_cards(view):
    # controls = [header, spacer, *item_cards]
    return view.controls[2:]


def test_three_items_rendered_in_order(state):
    page = FakePage()
    view = build_course_chapter_view(page, state, _CHAPTER)
    lessons = state.lesson_engine.lessons_in_category(_CHAPTER)

    cards = _item_cards(view)
    assert len(cards) == 3
    for card, lesson in zip(cards, lessons):
        title_text = card.content.controls[0].controls[1].value
        assert lesson.title in title_text


def test_only_first_item_unlocked_initially(state):
    page = FakePage()
    view = build_course_chapter_view(page, state, _CHAPTER)
    cards = _item_cards(view)

    assert cards[0].content.controls[2].disabled is False
    assert cards[1].content.controls[2].disabled is True
    assert cards[2].content.controls[2].disabled is True


def test_second_item_unlocks_after_first_completed(state):
    lessons = state.lesson_engine.lessons_in_category(_CHAPTER)
    state.progress.complete_lesson(lessons[0].id, lessons[0].reward_stars)

    page = FakePage()
    view = build_course_chapter_view(page, state, _CHAPTER)
    cards = _item_cards(view)

    assert cards[0].content.controls[1].value == "✅ Completed"
    assert cards[1].content.controls[2].disabled is False
    assert cards[2].content.controls[2].disabled is True


def test_non_quiz_item_navigates_to_lesson_route(state):
    lessons = state.lesson_engine.lessons_in_category(_CHAPTER)
    page = FakePage()
    view = build_course_chapter_view(page, state, _CHAPTER)
    cards = _item_cards(view)

    cards[0].content.controls[2].on_click(None)
    assert page.routes_visited == [f"/lesson/{lessons[0].id}"]


def test_quiz_item_navigates_to_course_quiz_route_once_unlocked(state):
    lessons = state.lesson_engine.lessons_in_category(_CHAPTER)
    state.progress.complete_lesson(lessons[0].id, lessons[0].reward_stars)
    state.progress.complete_lesson(lessons[1].id, lessons[1].reward_stars)

    page = FakePage()
    view = build_course_chapter_view(page, state, _CHAPTER)
    cards = _item_cards(view)

    assert lessons[2].is_quiz is True
    cards[2].content.controls[2].on_click(None)
    assert page.routes_visited == [f"/course-quiz/{lessons[2].id}"]
