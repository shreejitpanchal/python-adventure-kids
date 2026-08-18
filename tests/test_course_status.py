"""Tests for compute_course_status()/maybe_award_course_badge() -- the
"🎓 Python Learning" course dashboard's shared status view-model, exercised
against real LessonEngine/ProgressStore instances."""
from __future__ import annotations

import pytest

from app.engine.categories import COURSE_CATEGORIES
from app.engine.course_status import COURSE_BADGE_ID, compute_course_status, maybe_award_course_badge
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
    assert status.items_total == len(all_course_lesson_ids) == 18
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
    assert chapter.total_count == 3


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
