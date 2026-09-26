"""Exercises build_course_map_view()'s chapter grid and XP/progress header
-- built against a real AppState/LessonEngine, same pattern as
test_category_map_flet.py."""
from __future__ import annotations

import pytest

from app.engine.categories import COURSE_CATEGORIES, get_category_meta
from app.engine.course_status import compute_course_status
from app.engine.courses import PYTHON_COURSE
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
    # controls = [header, spacer, hud, spacer, Row(chapter_cards)]
    return view.controls[4].controls


def test_one_card_per_chapter_in_curriculum_order(state):
    page = FakePage()
    view = build_course_map_view(page, state)
    cards = _chapter_cards(view)

    assert len(cards) == len(COURSE_CATEGORIES)
    titles = [card.content.controls[0].controls[1].value for card in cards]
    assert titles == [get_category_meta(c).title for c in COURSE_CATEGORIES]


def test_chapter_card_status_starts_at_zero_of_its_total(state):
    page = FakePage()
    view = build_course_map_view(page, state)
    first_chapter = COURSE_CATEGORIES[0]
    total = len(state.lesson_engine.lessons_in_category(first_chapter))

    card = _chapter_cards(view)[0]
    assert card.content.controls[1].value == f"0/{total} items"


def test_data_structures_card_shows_0_of_9(state):
    page = FakePage()
    view = build_course_map_view(page, state)
    card = next(
        c for c in _chapter_cards(view)
        if c.content.controls[0].controls[1].value == get_category_meta("course_data_structures").title
    )
    assert card.content.controls[1].value == "0/9 items"


def test_variables_card_shows_0_of_6(state):
    page = FakePage()
    view = build_course_map_view(page, state)
    card = next(
        c for c in _chapter_cards(view)
        if c.content.controls[0].controls[1].value == get_category_meta("course_variables").title
    )
    assert card.content.controls[1].value == "0/6 items"


def test_chapter_card_click_navigates_to_its_chapter_route(state):
    page = FakePage()
    view = build_course_map_view(page, state)
    card = _chapter_cards(view)[0]

    button = card.content.controls[2]
    button.on_click(None)
    assert page.routes_visited == [f"/course/{COURSE_CATEGORIES[0]}"]


def test_header_is_a_hero_header_with_a_codey_line(state):
    from app.ui.components.adventure_kit_flet import find_by_kind
    from app.ui.course_map_flet import codey_course_line

    view = build_course_map_view(FakePage(), state)
    header = view.controls[0]
    assert header.data == {"kind": "hero_header", "title": PYTHON_COURSE.title}
    assert len(find_by_kind(header, "codey_companion")) == 1
    assert codey_course_line(0, 10, "X") == "A whole course to explore. Open Chapter 1 to begin!"
    assert "graduate" in codey_course_line(10, 10, "X")
    assert codey_course_line(3, 10, "X") == "3 of 10 lessons done. Pick a chapter and keep going!"


def test_hud_reflects_real_progress(state):
    first_chapter = COURSE_CATEGORIES[0]
    lessons = state.lesson_engine.lessons_in_category(first_chapter)
    state.progress.complete_lesson(lessons[0].id, lessons[0].reward_stars)

    page = FakePage()
    view = build_course_map_view(page, state)
    status = compute_course_status(state.lesson_engine, state.progress, COURSE_CATEGORIES)

    hud = view.controls[2]
    lessons_text = hud.content.controls[1]
    assert lessons_text.value == f"{status.items_done}/{status.items_total} lessons complete"


def test_chapter_card_shows_complete_once_every_item_done(state):
    first_chapter = COURSE_CATEGORIES[0]
    lessons = state.lesson_engine.lessons_in_category(first_chapter)
    for lesson in lessons:
        state.progress.complete_lesson(lesson.id, lesson.reward_stars)

    page = FakePage()
    view = build_course_map_view(page, state)
    card = _chapter_cards(view)[0]
    assert card.content.controls[1].value == "✅ Chapter complete!"
