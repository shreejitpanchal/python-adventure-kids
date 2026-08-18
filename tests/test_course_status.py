"""Tests for compute_course_status()/is_topic_item_unlocked()/
next_topic_item()/maybe_award_course_badge() -- the "🎓 Python Learning"
course dashboard's shared status view-model, exercised against real
LessonEngine/ProgressStore instances."""
from __future__ import annotations

import pytest

from app.engine.categories import COURSE_CATEGORIES
from app.engine.course_status import (
    COURSE_BADGE_ID, compute_course_status, is_topic_item_unlocked,
    maybe_award_course_badge, next_topic_item,
)
from app.engine.lesson_engine import LessonEngine
from app.progress.store import ProgressStore


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


@pytest.fixture
def progress(tmp_path):
    store = ProgressStore(tmp_path / "progress.sqlite3")
    yield store
    store.close()


@pytest.fixture(scope="module")
def all_course_lesson_ids(engine):
    return [
        lesson.id for category in COURSE_CATEGORIES for lesson in engine.lessons_in_category(category)
    ]


def test_status_starts_at_zero_done(engine, progress, all_course_lesson_ids):
    status = compute_course_status(engine, progress)
    assert status.items_total == len(all_course_lesson_ids)
    assert status.items_done == 0
    assert status.stars_earned == 0
    assert len(status.chapters) == len(COURSE_CATEGORIES)


def test_status_reflects_real_progress(engine, progress, all_course_lesson_ids):
    progress.complete_lesson(all_course_lesson_ids[0], 2)
    progress.complete_lesson(all_course_lesson_ids[1], 3)

    status = compute_course_status(engine, progress)
    assert status.items_done == 2
    assert status.stars_earned == 5


def test_chapter_status_reports_per_chapter_completion(engine, progress):
    first_chapter = COURSE_CATEGORIES[0]
    lessons = engine.lessons_in_category(first_chapter)
    progress.complete_lesson(lessons[0].id, lessons[0].reward_stars)

    status = compute_course_status(engine, progress)
    chapter = next(c for c in status.chapters if c.category == first_chapter)
    assert chapter.completed_count == 1
    assert chapter.total_count == len(lessons)


def test_data_structures_chapter_shows_0_of_12(engine, progress):
    status = compute_course_status(engine, progress)
    chapter = next(c for c in status.chapters if c.category == "course_data_structures")
    assert chapter.completed_count == 0
    assert chapter.total_count == 12
    assert [t.topic for t in chapter.topics] == ["Lists", "Tuples", "Dictionaries", "Sets"]
    for topic in chapter.topics:
        assert topic.total_count == 3


def test_variables_chapter_shows_0_of_15(engine, progress):
    status = compute_course_status(engine, progress)
    chapter = next(c for c in status.chapters if c.category == "course_variables")
    assert chapter.completed_count == 0
    assert chapter.total_count == 15
    assert [t.topic for t in chapter.topics] == ["Variables", "Numbers", "Strings", "Booleans", "Type Conversion"]


def test_intro_setup_chapter_shows_0_of_9(engine, progress):
    status = compute_course_status(engine, progress)
    chapter = next(c for c in status.chapters if c.category == "course_intro_setup")
    assert chapter.completed_count == 0
    assert chapter.total_count == 9
    assert [t.topic for t in chapter.topics] == ["Print", "Comments", "Reading Errors"]


def test_control_flow_chapter_shows_0_of_9(engine, progress):
    status = compute_course_status(engine, progress)
    chapter = next(c for c in status.chapters if c.category == "course_control_flow")
    assert chapter.completed_count == 0
    assert chapter.total_count == 9
    assert [t.topic for t in chapter.topics] == ["Conditionals", "For Loops", "While Loops"]


def test_functions_chapter_shows_0_of_9(engine, progress):
    status = compute_course_status(engine, progress)
    chapter = next(c for c in status.chapters if c.category == "course_functions")
    assert chapter.completed_count == 0
    assert chapter.total_count == 9
    assert [t.topic for t in chapter.topics] == ["Defining Functions", "Parameters", "Return Values"]


def test_badge_not_awarded_until_every_item_complete(engine, progress, all_course_lesson_ids):
    for lesson_id in all_course_lesson_ids[:-1]:
        progress.complete_lesson(lesson_id, 3)
    maybe_award_course_badge(engine, progress)
    assert COURSE_BADGE_ID not in progress.get_badge_ids()


def test_badge_awarded_once_every_item_complete(engine, progress, all_course_lesson_ids):
    for lesson_id in all_course_lesson_ids:
        progress.complete_lesson(lesson_id, 3)
    maybe_award_course_badge(engine, progress)
    assert COURSE_BADGE_ID in progress.get_badge_ids()


# -- topic-scoped unlocking: sibling topics never block each other --------
def test_first_item_of_every_topic_is_always_unlocked(engine):
    lessons = engine.lessons_in_category("course_data_structures")
    tuples_items = [l for l in lessons if l.topic == "Tuples"]
    assert is_topic_item_unlocked(tuples_items[0], tuples_items, completed_ids=[]) is True


def test_second_item_of_a_topic_locked_until_first_done(engine):
    lessons = engine.lessons_in_category("course_data_structures")
    tuples_items = [l for l in lessons if l.topic == "Tuples"]
    assert is_topic_item_unlocked(tuples_items[1], tuples_items, completed_ids=[]) is False
    assert is_topic_item_unlocked(tuples_items[1], tuples_items, completed_ids=[tuples_items[0].id]) is True


def test_sets_topic_never_blocked_by_lists_tuples_or_dictionaries(engine):
    """The core guarantee behind "all topics open": Sets' first item must
    be playable with zero course progress at all, even though its
    category_level (10) is numerically after Lists/Tuples/Dictionaries'
    items (1-9) in the same course_data_structures category."""
    lessons = engine.lessons_in_category("course_data_structures")
    sets_items = [l for l in lessons if l.topic == "Sets"]
    assert is_topic_item_unlocked(sets_items[0], sets_items, completed_ids=[]) is True


@pytest.mark.parametrize("category", [
    "course_intro_setup", "course_control_flow", "course_functions", "course_variables",
])
def test_last_topics_first_item_never_blocked_by_earlier_topics(engine, category):
    """Same "all topics open" guarantee as course_data_structures' Sets,
    generalized across every other multi-topic chapter -- the last topic's
    first item must be playable with zero progress, even though its
    category_level sorts after every earlier topic's items."""
    lessons = engine.lessons_in_category(category)
    last_topic = lessons[-1].topic
    last_topic_items = [l for l in lessons if l.topic == last_topic]
    assert is_topic_item_unlocked(last_topic_items[0], last_topic_items, completed_ids=[]) is True


def test_next_topic_item_finds_the_next_item_in_the_same_topic(engine):
    lessons = engine.lessons_in_category("course_data_structures")
    tuples_items = [l for l in lessons if l.topic == "Tuples"]

    next_item = next_topic_item(engine, tuples_items[0], completed_ids=[tuples_items[0].id])
    assert next_item.id == tuples_items[1].id


def test_next_topic_item_ignores_sibling_topics(engine):
    """Completing every Lists/Dictionaries/Sets item must not make
    next_topic_item() skip past Tuples' own items -- each topic's "next"
    lookup only ever considers its own items."""
    lessons = engine.lessons_in_category("course_data_structures")
    tuples_items = [l for l in lessons if l.topic == "Tuples"]
    other_ids = [l.id for l in lessons if l.topic != "Tuples"]

    completed = set(other_ids) | {tuples_items[0].id}
    next_item = next_topic_item(engine, tuples_items[0], completed_ids=completed)
    assert next_item.id == tuples_items[1].id


def test_next_topic_item_none_when_topic_fully_complete(engine):
    lessons = engine.lessons_in_category("course_data_structures")
    tuples_items = [l for l in lessons if l.topic == "Tuples"]
    completed = {l.id for l in tuples_items}

    assert next_topic_item(engine, tuples_items[-1], completed_ids=completed) is None
