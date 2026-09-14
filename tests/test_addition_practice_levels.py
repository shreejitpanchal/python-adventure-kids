"""Content checks for the "addition" bonus practice levels (category_level
2-37 currently): unedited starter code must not already satisfy the
challenge, and the intended solution must. Split out from the old combined
test_bonus_levels.py/test_bonus_levels_extended.py so each category can be
extended independently."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

BONUS_SOLUTIONS = {
    "lesson_21": "print(15 + 27)",
    "lesson_22": "print(4 + 6 + 9)",
    "lesson_67": "print(6 + 7 + 8 + 9)",
    "lesson_65": "print(3.5 + 2.25)",
    "lesson_72": "print(4.75 + 1.5)",
    "lesson_66": "print(15 + -6)",
    "lesson_77": "print(-9 + -14)",
    "lesson_68": "print(round(5.6 + 3.1))",
    "lesson_71": "print(round(7.8 + 2.9))",
    "lesson_69": "print(abs(-20 + 6))",
    "lesson_75": "print(abs(-25 + 9))",
    "lesson_70": "print(4 + 3 > 10)",
    "lesson_78": "print(7 + 9 > 10)",
    "lesson_74": 'print(int("20") + 8)',
    "lesson_80": 'print(int("45") + 9)',
    "lesson_76": "print(6 + 6 == 11)",
    "lesson_81": "print(7 + 5 == 13)",
    "lesson_79": "print((4 + 6) ** 2)",
    "lesson_520": "print((7 + 3) ** 2)",
    "lesson_521": "print((18 + 24) // 5)",
    "lesson_528": "print((26 + 19) // 5)",
    "lesson_522": "print((27 + 18) % 8)",
    "lesson_531": "print((23 + 19) % 7)",
    "lesson_523": 'print(f"Total: {12 + 9}")',
    "lesson_532": 'print(f"Result: {14 + 8}")',
    "lesson_73": "print(max(4 + 4, 2 + 9))",
    "lesson_525": "print(max(5 + 5 + 5, 3 + 4 + 9))",
    "lesson_534": "print(min(5 + 5, 2 + 9))",
    "lesson_530": "print(min(4 + 9 + 2, 6 + 6 + 6))",
    "lesson_527": "print((14 + 13) % 4 == 0)",
    "lesson_524": "print(10.25 + -4.5 + 2.25)",
    "lesson_526": 'print(f"Sum: {round(5.6 + 3.1)}")',
    "lesson_529": 'print(f"Result: {4 + 3 > 10}")',
    "lesson_536": "print(max(7 + 7, 5 + 9), 20 + 3 > 25)",
    "lesson_533": 'print(f"{6 + 9} and {14 + 8}")',
    "lesson_539": 'print(f"{round(4.25 + 1.75 + 2.0)}", 12 + 9 + 6 > 25)',
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


def test_addition_category_has_a_full_1_to_37_level_progression(engine):
    lessons = engine.lessons_in_category("addition")
    assert len(lessons) == 37
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 38))
