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
    assert len(addition_lessons) == 3  # lesson_03 + two bonus levels


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


# -- main path vs bonus levels ---------------------------------------------
def test_main_path_lessons_excludes_bonus_levels(engine):
    main_path_ids = {lesson.id for lesson in engine.main_path_lessons()}
    assert "lesson_03" in main_path_ids  # addition level 1 is on the guided path
    assert "lesson_21" not in main_path_ids  # addition level 2 is bonus-only
    assert "lesson_22" not in main_path_ids


def test_bonus_levels_are_not_chained_via_next_after(engine):
    bonus = engine.get("lesson_21")
    assert bonus.next_lesson_id is None
    assert engine.next_after("lesson_21") is None


def test_main_path_lesson_18_has_no_next_even_though_bonus_levels_sort_after_it(engine):
    # lesson_18 is the last main-path lesson; bonus levels 19-28 sort after it
    # by `level`, but next_after must not fall through to them.
    assert engine.next_after("lesson_18") is None


def test_resolve_current_never_returns_a_bonus_level(engine):
    lesson = engine.resolve_current(completed_ids=[], stored_current_id=None)
    assert lesson.main_path is True

    # even if a bonus level id is (incorrectly) passed as the stored pointer,
    # it's still a valid lookup -- but resolve_current's *fallback* path
    # must never land on one.
    all_main_ids = [l.id for l in engine.main_path_lessons()]
    lesson = engine.resolve_current(completed_ids=all_main_ids, stored_current_id=None)
    assert lesson.main_path is True
