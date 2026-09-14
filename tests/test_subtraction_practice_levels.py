"""Content checks for the "subtraction" bonus practice levels (category_level
2-37 currently): unedited starter code must not already satisfy the
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
    "lesson_84": "print(50 - 5 - 10 - 15)",
    "lesson_82": "print(6.75 - 2.5)",
    "lesson_89": "print(9.5 - 2.25)",
    "lesson_83": "print(15 - -6)",
    "lesson_94": "print(-20 - -8)",
    "lesson_85": "print(round(12.7 - 4.3))",
    "lesson_88": "print(round(15.6 - 3.8))",
    "lesson_86": "print(abs(6 - 25))",
    "lesson_92": "print(abs(8 - 30))",
    "lesson_87": "print(9 - 8 > 5)",
    "lesson_95": "print(9 - 7 > 5)",
    "lesson_91": 'print(int("30") - 12)',
    "lesson_97": 'print(int("45") - 9)',
    "lesson_93": "print(15 - 5 == 11)",
    "lesson_98": "print(14 - 3 == 12)",
    "lesson_96": "print((15 - 7) ** 2)",
    "lesson_540": "print((13 - 6) ** 2)",
    "lesson_541": "print((50 - 14) // 4)",
    "lesson_548": "print((45 - 14) // 5)",
    "lesson_542": "print((35 - 8) % 6)",
    "lesson_551": "print((40 - 9) % 7)",
    "lesson_543": 'print(f"Left: {30 - 12}")',
    "lesson_552": 'print(f"Remaining: {35 - 19}")',
    "lesson_554": "print(max(15 - 4, 9 - 1))",
    "lesson_550": "print(max(30 - 6 - 4, 25 - 2 - 8))",
    "lesson_90": "print(min(20 - 5, 15 - 2))",
    "lesson_545": "print(min(40 - 10 - 15, 35 - 5 - 20))",
    "lesson_547": "print((27 - 9) % 4 == 0)",
    "lesson_544": "print(15.25 - 4.25 - -2.5)",
    "lesson_546": 'print(f"Diff: {round(12.7 - 4.3)}")',
    "lesson_549": 'print(f"Result: {9 - 8 > 5}")',
    "lesson_556": "print(min(20 - 9, 30 - 25), 20 - 9 == 10)",
    "lesson_553": 'print(f"{25 - 9} and {40 - 15}")',
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


def test_subtraction_category_has_a_full_1_to_37_level_progression(engine):
    lessons = engine.lessons_in_category("subtraction")
    assert len(lessons) == 37
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 38))
