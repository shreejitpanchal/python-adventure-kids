"""Tests for category grouping, unlocking, and the main-path/bonus-level split."""
import pytest

from app.engine.categories import CATEGORY_META, get_category_meta
from app.engine.lesson_engine import LessonEngine


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_categories_lists_every_category_once_in_curriculum_order(engine):
    categories = engine.categories()
    assert len(categories) == len(set(categories)), "categories() must not repeat"
    assert categories[0] == "basics"
    assert "numbers" in categories
    assert "addition" in categories


def test_lessons_in_category_sorted_by_category_level(engine):
    addition_lessons = engine.lessons_in_category("addition")
    levels = [lesson.category_level for lesson in addition_lessons]
    assert levels == sorted(levels)
    assert len(addition_lessons) == 20  # lesson_03 + 19 bonus levels (2-20)


def test_lessons_in_category_unknown_category_returns_empty(engine):
    assert engine.lessons_in_category("does_not_exist") == []


def test_every_category_has_display_metadata(engine):
    for category in engine.categories():
        assert category in CATEGORY_META, f"'{category}' has no entry in CATEGORY_META"


def test_get_category_meta_falls_back_for_unknown_category():
    meta = get_category_meta("something_new")
    assert meta.title
    assert meta.icon


# -- unlocking ------------------------------------------------------------
def test_level_1_is_always_unlocked(engine):
    lesson = engine.get("lesson_03")  # addition level 1
    assert engine.is_unlocked(lesson, completed_ids=[]) is True


def test_level_2_locked_until_level_1_complete(engine):
    lesson = engine.get("lesson_21")  # addition level 2
    assert engine.is_unlocked(lesson, completed_ids=[]) is False
    assert engine.is_unlocked(lesson, completed_ids=["lesson_03"]) is True


def test_level_3_locked_until_levels_1_and_2_complete(engine):
    lesson = engine.get("lesson_22")  # addition level 3
    assert engine.is_unlocked(lesson, completed_ids=["lesson_03"]) is False
    assert engine.is_unlocked(lesson, completed_ids=["lesson_03", "lesson_21"]) is True


def test_next_unlocked_in_category_returns_first_incomplete_unlocked_level(engine):
    lesson = engine.next_unlocked_in_category("addition", completed_ids=[])
    assert lesson.id == "lesson_03"

    lesson = engine.next_unlocked_in_category("addition", completed_ids=["lesson_03"])
    assert lesson.id == "lesson_21"


def test_next_unlocked_in_category_none_when_all_complete(engine):
    all_addition_ids = [lesson.id for lesson in engine.lessons_in_category("addition")]
    assert engine.next_unlocked_in_category("addition", completed_ids=all_addition_ids) is None


# -- Today's Mission: the computed round-robin across TODAYS_MISSION_CATEGORIES
def test_main_path_lessons_includes_every_level_of_the_core_categories(engine):
    main_path_ids = {lesson.id for lesson in engine.main_path_lessons()}
    assert "lesson_03" in main_path_ids  # addition level 1
    assert "lesson_21" in main_path_ids  # addition level 2 -- part of the round-robin
    assert "lesson_22" in main_path_ids  # addition level 3


def test_main_path_lessons_excludes_categories_outside_the_rotation(engine):
    main_path_ids = {lesson.id for lesson in engine.main_path_lessons()}
    games_ids = {lesson.id for lesson in engine.lessons_in_category("games")}
    snake_ids = {lesson.id for lesson in engine.lessons_in_category("snake")}
    assert not (games_ids & main_path_ids)
    assert not (snake_ids & main_path_ids)


def test_next_after_continues_into_the_next_categorys_same_level(engine):
    # lesson_03 = addition level 1; subtraction is next in
    # TODAYS_MISSION_CATEGORIES order, still at level 1.
    next_lesson = engine.next_after("lesson_03")
    assert next_lesson.category == "subtraction"
    assert next_lesson.category_level == 1


def test_next_after_moves_to_level_2_once_every_categorys_level_1_is_done(engine):
    # lesson_13 = lists level 1, the last category in TODAYS_MISSION_CATEGORIES
    # order -- the next mission step should wrap to numbers' level 2, not
    # spill into games/Snake just because they sort after lesson_13 by `level`.
    next_lesson = engine.next_after("lesson_13")
    assert next_lesson.category == "numbers"
    assert next_lesson.category_level == 2


def test_next_after_a_lesson_outside_the_rotation_is_none(engine):
    # lesson_18 (Snake) isn't part of TODAYS_MISSION_CATEGORIES or the basics
    # intro, so it's simply not found in the computed sequence.
    assert engine.next_after("lesson_18") is None


def test_resolve_current_stays_within_the_computed_mission_sequence(engine):
    mission_ids = {lesson.id for lesson in engine.main_path_lessons()}
    lesson = engine.resolve_current(completed_ids=[], stored_current_id=None)
    assert lesson.id in mission_ids

    all_main_ids = [l.id for l in engine.main_path_lessons()]
    lesson = engine.resolve_current(completed_ids=all_main_ids, stored_current_id=None)
    assert lesson.id == engine.main_path_lessons()[-1].id
