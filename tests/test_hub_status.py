"""Tests for compute_hub_status() -- the Learning Hub's shared status
view-model, exercised against real LessonEngine/ProgressStore instances."""
from __future__ import annotations

import pytest

from app.config.settings import Settings
from app.engine.hub_status import compute_hub_status
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


def test_guided_status_shows_the_next_lesson_category_and_level(engine, progress):
    status = compute_hub_status(engine, progress, Settings())
    assert status.guided_status == "Next: Python Basics — Level 1"


def test_guided_status_advances_as_lessons_complete(engine, progress):
    progress.complete_lesson("lesson_01", 3)
    status = compute_hub_status(engine, progress, Settings())
    assert status.guided_status == "Next: Numbers — Level 1"


def test_project_status_reports_the_fixed_category_count(engine, progress):
    status = compute_hub_status(engine, progress, Settings())
    assert status.project_status == "6 categories available"


def test_cracker_status_starts_at_zero_solved(engine, progress):
    status = compute_hub_status(engine, progress, Settings())
    total = len(engine.lessons_in_category("code_crackers"))
    assert status.cracker_status == f"0/{total} solved"


def test_cracker_status_reflects_real_progress(engine, progress):
    cracker_ids = [lesson.id for lesson in engine.lessons_in_category("code_crackers")]
    for lesson_id in cracker_ids[:5]:
        progress.complete_lesson(lesson_id, 3)

    status = compute_hub_status(engine, progress, Settings())
    total = len(cracker_ids)
    assert status.cracker_status == f"5/{total} solved"


def test_advanced_cracker_status_reflects_real_progress(engine, progress):
    advanced_ids = [lesson.id for lesson in engine.lessons_in_category("advanced_code_crackers")]
    for lesson_id in advanced_ids[:3]:
        progress.complete_lesson(lesson_id, 3)

    status = compute_hub_status(engine, progress, Settings())
    total = len(advanced_ids)
    assert status.advanced_cracker_status == f"3/{total} solved"


def test_resume_label_is_none_when_no_route_is_stored(engine, progress):
    status = compute_hub_status(engine, progress, Settings(last_learning_route=""))
    assert status.resume_label is None


def test_resume_label_is_none_for_an_unrecognized_route_key(engine, progress):
    status = compute_hub_status(engine, progress, Settings(last_learning_route="not_a_real_key"))
    assert status.resume_label is None


@pytest.mark.parametrize(
    "route_key,expected_label",
    [
        ("guided", "Today's Mission"),
        ("code_crackers", "Code Cracker Puzzles"),
        ("advanced_code_crackers", "Advanced Code Crackers"),
        ("projects", "Build a Project"),
        ("course", "Python Learning"),
    ],
)
def test_resume_label_reflects_the_stored_route(engine, progress, route_key, expected_label):
    status = compute_hub_status(engine, progress, Settings(last_learning_route=route_key))
    assert status.resume_label == f"Continue where you left off: {expected_label}"


def test_course_status_starts_at_zero_complete(engine, progress):
    from app.engine.categories import COURSE_CATEGORIES

    status = compute_hub_status(engine, progress, Settings())
    total = sum(len(engine.lessons_in_category(category)) for category in COURSE_CATEGORIES)
    assert status.course_status == f"0/{total} lessons complete"


def test_course_status_reflects_real_progress(engine, progress):
    from app.engine.categories import COURSE_CATEGORIES

    all_ids = [
        lesson.id for category in COURSE_CATEGORIES for lesson in engine.lessons_in_category(category)
    ]
    for lesson_id in all_ids[:2]:
        progress.complete_lesson(lesson_id, 3)

    status = compute_hub_status(engine, progress, Settings())
    total = len(all_ids)
    assert status.course_status == f"2/{total} lessons complete"
