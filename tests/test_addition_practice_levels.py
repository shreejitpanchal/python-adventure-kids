"""Content checks for the "addition" bonus practice levels (category_level
2-20 currently): unedited starter code must not already satisfy the
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
    "lesson_65": "print(3.5 + 2.25)",
    "lesson_66": "print(15 + -6)",
    "lesson_67": "print(6 + 7 + 8 + 9)",
    "lesson_68": "print(round(5.6 + 3.1))",
    "lesson_69": "print(abs(-20 + 6))",
    "lesson_70": "print(4 + 3 > 10)",
    "lesson_71": "print(2 + 2 + 2 + 2 + 2)",
    "lesson_72": "print(4.75 + 1.5)",
    "lesson_73": "print(max(4 + 4, 2 + 9))",
    "lesson_74": 'print(int("20") + 8)',
    "lesson_75": "print(10 + 20 + 30 + 40 + 50)",
    "lesson_76": "print(6 + 6 == 11)",
    "lesson_77": "print(-9 + -14)",
    "lesson_78": "print(2.5 + 4.5 + 1.5)",
    "lesson_79": "print((4 + 6) ** 2)",
    "lesson_80": "print(5 + 10 + 15 + 20 + 25 + 30)",
    "lesson_81": "print(round(4.5 + 1.5), 8 + 8 > 20)",
    "lesson_520": "print(20 + -8 + 6)",
    "lesson_521": "print((18 + 24) // 5)",
    "lesson_522": "print((27 + 18) % 8)",
    "lesson_523": 'print(f"Total: {12 + 9}")',
    "lesson_524": "print(10.25 + -4.5 + 2.25)",
    "lesson_525": "print(max(5 + 5 + 5, 3 + 4 + 9))",
    "lesson_526": 'print(f"Sum: {round(5.6 + 3.1)}")',
    "lesson_527": "print((14 + 13) % 4 == 0)",
    "lesson_528": "print(20.25 + -5.25 + 6.5 + -2.5 + 1.0)",
    "lesson_529": 'print(f"Result: {4 + 3 > 10}")',
    "lesson_530": "print(min(4 + 9 + 2, 6 + 6 + 6))",
    "lesson_531": 'print((int("22") + 13) % 5)',
    "lesson_532": "print(abs(-20 + 5 + -12))",
    "lesson_533": 'print(f"{6 + 9} and {14 + 8}")',
    "lesson_534": "print((2 + 3 + 4) ** 2)",
    "lesson_535": "print(10.5 + -8.5 + 1.0 > 5)",
    "lesson_536": "print(max(7 + 7, 5 + 9), 20 + 3 > 25)",
    "lesson_537": 'print(f"Total: {round(4.5678 + 1.2345, 2)}")',
    "lesson_538": 'print(int("22") + int("8") + 7)',
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


def test_addition_category_has_a_full_1_to_40_level_progression(engine):
    lessons = engine.lessons_in_category("addition")
    assert len(lessons) == 40
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 41))
