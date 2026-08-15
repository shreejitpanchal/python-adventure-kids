"""Content checks for the Code Crackers debugging track: each lesson's
starter_code must be genuinely broken (fails to run, or runs but produces
the wrong output) and its example_code must be the working fix -- runs
cleanly, matches expected_output, and satisfies ast_contains."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_ast_contains, validate_output
from app.sandbox.runner import run_code

CRACKER_IDS = [f"cracker_{i:02d}" for i in range(1, 11)]


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_all_ten_code_crackers_are_registered(engine):
    crackers = engine.lessons_in_category("code_crackers")
    assert {lesson.id for lesson in crackers} == set(CRACKER_IDS)
    assert sorted(lesson.category_level for lesson in crackers) == list(range(1, 11))


@pytest.mark.parametrize("lesson_id", CRACKER_IDS)
def test_is_a_bonus_level_with_ast_contains_set(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert lesson.main_path is False
    assert lesson.next_lesson_id is None
    assert lesson.ast_contains, f"{lesson_id} should declare ast_contains"


@pytest.mark.parametrize("lesson_id", CRACKER_IDS)
def test_starter_code_is_genuinely_broken(engine, lesson_id):
    lesson = engine.get(lesson_id)
    result = run_code(lesson.starter_code.strip())
    passes = result.success and validate_output(result.stdout, lesson.expected_output)
    assert not passes, f"{lesson_id}'s starter_code unexpectedly already satisfies the challenge"


@pytest.mark.parametrize("lesson_id", CRACKER_IDS)
def test_example_code_is_the_working_fix(engine, lesson_id):
    lesson = engine.get(lesson_id)
    result = run_code(lesson.example_code.strip())
    assert result.success is True, f"{lesson_id} example_code failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is True, (
        f"{lesson_id} example_code produced {result.stdout!r}, expected {lesson.expected_output!r}"
    )
    assert validate_ast_contains(lesson.example_code, lesson.ast_contains) is True, (
        f"{lesson_id} example_code doesn't satisfy its own ast_contains: {lesson.ast_contains}"
    )
