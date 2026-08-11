"""End-to-end simulation of what the lesson screen does on a successful run,
without needing the actual GUI: load lesson -> run code -> validate -> award progress.
"""
from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.progress.store import ProgressStore
from app.sandbox.runner import run_code


def test_full_successful_lesson_attempt(tmp_path):
    engine = LessonEngine()
    lesson = engine.first()
    store = ProgressStore(tmp_path / "progress.sqlite3")
    try:
        result = run_code(lesson.starter_code.strip())
        assert result.success is True
        assert validate_output(result.stdout, lesson.expected_output) is True

        assert store.is_lesson_completed(lesson.id) is False
        store.complete_lesson(lesson.id, lesson.reward_stars)
        badge_awarded = store.award_badge(lesson.badge) if lesson.badge else False

        summary = store.get_summary()
        assert store.is_lesson_completed(lesson.id) is True
        assert summary.total_stars == lesson.reward_stars
        assert summary.lessons_completed == 1
        if lesson.badge:
            assert badge_awarded is True
            assert lesson.badge in store.get_badge_ids()
    finally:
        store.close()


def test_wrong_output_does_not_complete_lesson(tmp_path):
    engine = LessonEngine()
    lesson = engine.first()
    store = ProgressStore(tmp_path / "progress.sqlite3")
    try:
        result = run_code('print("Not the expected text")')
        assert result.success is True
        assert validate_output(result.stdout, lesson.expected_output) is False
        assert store.is_lesson_completed(lesson.id) is False
    finally:
        store.close()
