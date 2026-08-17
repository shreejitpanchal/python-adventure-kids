"""Content checks for the "subtraction" bonus practice levels (category_level
2-20 currently): unedited starter code must not already satisfy the
challenge, and the intended solution must. Split out from the old combined
test_bonus_levels.py/test_bonus_levels_extended.py so each category can be
extended independently."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

BONUS_SOLUTIONS = {
    "lesson_23": "print(50 - 18)",
    "lesson_24": "print(30 - 12 - 5)",
    "lesson_82": "print(6.75 - 2.5)",
    "lesson_83": "print(15 - -6)",
    "lesson_84": "print(50 - 5 - 10 - 15)",
    "lesson_85": "print(round(12.7 - 4.3))",
    "lesson_86": "print(abs(6 - 25))",
    "lesson_87": "print(9 - 8 > 5)",
    "lesson_88": "print(100 - 20 - 20 - 20 - 20 - 20)",
    "lesson_89": "print(9.5 - 2.25)",
    "lesson_90": "print(min(20 - 5, 15 - 2))",
    "lesson_91": 'print(int("30") - 12)',
    "lesson_92": "print(200 - 10 - 20 - 30 - 40 - 50)",
    "lesson_93": "print(15 - 5 == 11)",
    "lesson_94": "print(-20 - -8)",
    "lesson_95": "print(30.5 - 8.25 - 4.5)",
    "lesson_96": "print((15 - 7) ** 2)",
    "lesson_97": "print(100 - 5 - 10 - 15 - 20 - 25)",
    "lesson_98": "print(round(12.5 - 4.5), 30 - 25 > 10)",
    "lesson_540": "print(30 - 8 - -4)",
    "lesson_541": "print((50 - 14) // 4)",
    "lesson_542": "print((35 - 8) % 6)",
    "lesson_543": 'print(f"Left: {30 - 12}")',
    "lesson_544": "print(15.25 - 4.25 - -2.5)",
    "lesson_545": "print(min(40 - 10 - 15, 35 - 5 - 20))",
    "lesson_546": 'print(f"Diff: {round(12.7 - 4.3)}")',
    "lesson_547": "print((27 - 9) % 4 == 0)",
    "lesson_548": "print(25.25 - 4.25 - -2.5 - 3.0 - -1.0)",
    "lesson_549": 'print(f"Result: {9 - 8 > 5}")',
    "lesson_550": "print(max(30 - 6 - 4, 25 - 2 - 8))",
    "lesson_551": 'print((int("42") - 7) % 6)',
    "lesson_552": "print(abs(6 - 20 - 9))",
    "lesson_553": 'print(f"{25 - 9} and {40 - 15}")',
    "lesson_554": "print((20 - 5 - 6) ** 2)",
    "lesson_555": "print(15.5 - 8.5 - -1.0 > 10)",
    "lesson_556": "print(min(20 - 9, 30 - 25), 20 - 9 == 10)",
    "lesson_557": 'print(f"Diff: {round(12.6789 - 4.1234, 2)}")',
    "lesson_558": 'print(int("50") - int("12") - 8)',
    "lesson_559": 'print(f"{round(15.75 - 4.25 - 3.5)}", 30 - 8 - 10 > 15)',
}


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


@pytest.mark.parametrize("lesson_id", list(BONUS_SOLUTIONS))
def test_bonus_level_is_marked_correctly(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert lesson.main_path is False
    assert lesson.category_level >= 2
    assert lesson.next_lesson_id is None


@pytest.mark.parametrize("lesson_id", list(BONUS_SOLUTIONS))
def test_unedited_starter_code_does_not_satisfy_the_challenge(engine, lesson_id):
    lesson = engine.get(lesson_id)
    result = run_code(lesson.starter_code.strip())
    assert result.success is True, f"{lesson_id} starter code failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is False, (
        f"{lesson_id}'s starter code already satisfies the challenge without editing"
    )


@pytest.mark.parametrize("lesson_id,solution", BONUS_SOLUTIONS.items())
def test_intended_solution_satisfies_the_challenge(engine, lesson_id, solution):
    lesson = engine.get(lesson_id)
    result = run_code(solution)
    assert result.success is True, f"{lesson_id} solution failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is True, (
        f"{lesson_id}'s intended solution produced {result.stdout!r}, expected {lesson.expected_output!r}"
    )


def test_subtraction_category_has_a_full_1_to_40_level_progression(engine):
    lessons = engine.lessons_in_category("subtraction")
    assert len(lessons) == 40
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 41))
