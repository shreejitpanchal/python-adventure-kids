"""Exercises build_course_chapter_view()'s item list -- gating, status
text, and quiz-vs-lesson routing -- against a real AppState/LessonEngine,
same pattern as test_category_map_flet.py."""
from __future__ import annotations

import flet as ft
import pytest

from app.engine.categories import get_topic_icon
from app.ui.app_state_flet import AppState
from app.ui.course_chapter_flet import build_course_chapter_view

# course_capstone is the one chapter left with no topic sub-grouping
# (every other chapter now splits into several named topics) -- used here
# to exercise the plain flat-3-item rendering path.
_CHAPTER = "course_capstone"


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


# -- multi-topic chapters (course_data_structures: Lists/Tuples/Dictionaries/Sets) --
def test_data_structures_chapter_renders_four_topic_headers_and_12_items(state):
    page = FakePage()
    view = build_course_chapter_view(page, state, "course_data_structures")
    rest = view.controls[2:]

    headers = [c for c in rest if isinstance(c, ft.Row)]
    items = [c for c in rest if isinstance(c, ft.Container)]
    expected_topics = ["Lists", "Tuples", "Dictionaries", "Sets"]
    assert [h.controls[0].value for h in headers] == [f"{get_topic_icon(t)} {t}" for t in expected_topics]
    assert len(items) == 12


def test_sets_first_item_unlocked_even_with_zero_progress(state):
    """The "all topics open" guarantee, exercised through the real screen:
    Sets' first item must be clickable even though nothing else in the
    chapter (Lists/Tuples/Dictionaries) has been touched."""
    page = FakePage()
    view = build_course_chapter_view(page, state, "course_data_structures")
    lessons = state.lesson_engine.lessons_in_category("course_data_structures")
    sets_first = min((l for l in lessons if l.topic == "Sets"), key=lambda l: l.category_level)

    items = [c for c in view.controls[2:] if isinstance(c, ft.Container)]
    card = next(c for c in items if sets_first.title in c.content.controls[0].controls[1].value)
    assert card.content.controls[2].disabled is False


def test_item_numbering_resets_at_the_start_of_each_topic(state):
    page = FakePage()
    view = build_course_chapter_view(page, state, "course_data_structures")
    items = [c for c in view.controls[2:] if isinstance(c, ft.Container)]

    # First item of every topic (indices 0, 3, 6, 9) is badge "1", not a
    # running chapter-wide count.
    for index in (0, 3, 6, 9):
        badge_text = items[index].content.controls[0].controls[0].content.value
        assert badge_text == "1"


# -- the other 3 chapters expanded into multiple topics --------------------
@pytest.mark.parametrize("category,expected_topics", [
    ("course_intro_setup", ["Print", "Comments", "Reading Errors"]),
    ("course_control_flow", ["Conditionals", "For Loops", "While Loops"]),
    ("course_functions", ["Defining Functions", "Parameters", "Return Values"]),
])
def test_chapter_renders_three_topic_headers_and_nine_items(state, category, expected_topics):
    page = FakePage()
    view = build_course_chapter_view(page, state, category)
    rest = view.controls[2:]

    headers = [c for c in rest if isinstance(c, ft.Row)]
    items = [c for c in rest if isinstance(c, ft.Container)]
    assert [h.controls[0].value for h in headers] == [f"{get_topic_icon(t)} {t}" for t in expected_topics]
    assert len(items) == 9


@pytest.mark.parametrize("category", ["course_intro_setup", "course_control_flow", "course_functions"])
def test_third_topics_first_item_unlocked_even_with_zero_progress(state, category):
    """Same "all topics open" guarantee as Data Structures' Sets, exercised
    for each newly-expanded chapter's last topic."""
    page = FakePage()
    view = build_course_chapter_view(page, state, category)
    lessons = state.lesson_engine.lessons_in_category(category)
    last_topic = lessons[-1].topic
    first_of_last_topic = min((l for l in lessons if l.topic == last_topic), key=lambda l: l.category_level)

    items = [c for c in view.controls[2:] if isinstance(c, ft.Container)]
    card = next(c for c in items if first_of_last_topic.title in c.content.controls[0].controls[1].value)
    assert card.content.controls[2].disabled is False
