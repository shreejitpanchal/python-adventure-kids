"""Tests for compute_course_status()/maybe_award_course_badge() applied to
the "🤖 AI & Machine Learning" course -- mirrors test_course_status.py's
pattern, exercising the same (now course-parameterized) engine functions
against AI_ML_COURSE's own categories/badge instead of the Python course's."""
from __future__ import annotations

import pytest

from app.engine.course_status import compute_course_status, maybe_award_course_badge
from app.engine.courses import AI_ML_COURSE
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
def all_ai_course_lesson_ids(engine):
    return [
        lesson.id for category in AI_ML_COURSE.categories for lesson in engine.lessons_in_category(category)
    ]


def test_status_starts_at_zero_done(engine, progress, all_ai_course_lesson_ids):
    status = compute_course_status(engine, progress, AI_ML_COURSE.categories)
    assert status.items_total == len(all_ai_course_lesson_ids)
    assert status.items_done == 0
    assert status.stars_earned == 0
    assert len(status.chapters) == len(AI_ML_COURSE.categories)


def test_status_reflects_real_progress(engine, progress, all_ai_course_lesson_ids):
    progress.complete_lesson(all_ai_course_lesson_ids[0], 2)
    progress.complete_lesson(all_ai_course_lesson_ids[1], 3)

    status = compute_course_status(engine, progress, AI_ML_COURSE.categories)
    assert status.items_done == 2
    assert status.stars_earned == 5


def test_ai_foundations_chapter_shows_0_of_9(engine, progress):
    status = compute_course_status(engine, progress, AI_ML_COURSE.categories)
    chapter = next(c for c in status.chapters if c.category == "ai_foundations")
    assert chapter.completed_count == 0
    assert chapter.total_count == 9
    assert [t.topic for t in chapter.topics] == ["What is AI?", "Rule-Based Decisions", "Types of AI"]
    for topic in chapter.topics:
        assert topic.total_count == 3


def test_ai_tools_chapter_shows_0_of_6(engine, progress):
    status = compute_course_status(engine, progress, AI_ML_COURSE.categories)
    chapter = next(c for c in status.chapters if c.category == "ai_tools")
    assert chapter.completed_count == 0
    assert chapter.total_count == 6
    assert [t.topic for t in chapter.topics] == ["What is Machine Learning?", "What is MCP?"]
    for topic in chapter.topics:
        assert topic.total_count == 3


def test_ai_advanced_chapter_shows_0_of_6(engine, progress):
    status = compute_course_status(engine, progress, AI_ML_COURSE.categories)
    chapter = next(c for c in status.chapters if c.category == "ai_advanced")
    assert chapter.completed_count == 0
    assert chapter.total_count == 6
    assert [t.topic for t in chapter.topics] == ["Neural Networks", "MCP Framework"]
    for topic in chapter.topics:
        assert topic.total_count == 3


def test_badge_not_awarded_until_every_item_complete(engine, progress, all_ai_course_lesson_ids):
    for lesson_id in all_ai_course_lesson_ids[:-1]:
        progress.complete_lesson(lesson_id, 3)
    maybe_award_course_badge(engine, progress, AI_ML_COURSE.categories, AI_ML_COURSE.badge_id)
    assert AI_ML_COURSE.badge_id not in progress.get_badge_ids()


def test_badge_awarded_once_every_item_complete(engine, progress, all_ai_course_lesson_ids):
    for lesson_id in all_ai_course_lesson_ids:
        progress.complete_lesson(lesson_id, 3)
    maybe_award_course_badge(engine, progress, AI_ML_COURSE.categories, AI_ML_COURSE.badge_id)
    assert AI_ML_COURSE.badge_id in progress.get_badge_ids()


def test_ai_and_python_courses_are_independent_categories(engine):
    """The two courses must never share a category -- otherwise a lesson
    would ambiguously belong to both courses' status/badge accounting."""
    from app.engine.categories import COURSE_CATEGORIES

    assert set(AI_ML_COURSE.categories).isdisjoint(set(COURSE_CATEGORIES))
