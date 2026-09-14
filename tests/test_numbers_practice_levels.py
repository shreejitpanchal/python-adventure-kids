"""Content checks for the "numbers" bonus practice levels (category_level
2-40 currently): unedited starter code must not already satisfy the
challenge, and the intended solution must. Split out from the old combined
test_bonus_levels.py/test_bonus_levels_extended.py so each category can be
extended independently."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

BONUS_SOLUTIONS = {
    "lesson_19": "print(42)",
    "lesson_48": "print(-12)",
    "lesson_20": "print(-20)",
    "lesson_49": "print(4.25)",
    "lesson_63": "print(9.75)",
    "lesson_50": "print(8, 20)",
    "lesson_64": "print(6, 30)",
    "lesson_51": "print(abs(-14))",
    "lesson_61": "print(abs(-12.25))",
    "lesson_52": "print(round(4.2))",
    "lesson_60": "print(round(-8.6))",
    "lesson_53": "print(3 > 10)",
    "lesson_504": "print(15 > 6)",
    "lesson_54": "print(5 == 9)",
    "lesson_507": "print(12 == 15)",
    "lesson_55": "print(10 != 10)",
    "lesson_509": "print(14 != 14)",
    "lesson_56": "print(max(23, 17))",
    "lesson_510": "print(max(48, 31))",
    "lesson_57": "print(min(31, 19))",
    "lesson_511": "print(min(44, 27))",
    "lesson_58": "print(3 ** 4)",
    "lesson_62": "print((-3) ** 2)",
    "lesson_59": 'print(int("15") + 5)',
    "lesson_513": 'print(int("36") + 9)',
    "lesson_500": "print(23 // 5)",
    "lesson_514": "print(26 // 4)",
    "lesson_501": "print(23 % 5)",
    "lesson_517": "print(29 % 6)",
    "lesson_503": "print(round(8.36219, 2))",
    "lesson_508": "print(round(-8.6789, 2))",
    "lesson_505": "print(10 < 5 < 20)",
    "lesson_515": "print(-10 < -15 < 0)",
    "lesson_502": "print(29 // 4, 29 % 4)",
    "lesson_506": "print(17 % 5 == 0)",
    "lesson_512": "print(round(abs(-12.3456), 2))",
    "lesson_516": "print(3 ** 4 // 7)",
    "lesson_518": 'print(int("40") % 7)',
    "lesson_519": "print(round(9.8765, 2), 34 // 6, 34 % 6 == 4)",
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


def test_numbers_category_has_a_full_1_to_40_level_progression(engine):
    lessons = engine.lessons_in_category("numbers")
    assert len(lessons) == 40
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 41))
