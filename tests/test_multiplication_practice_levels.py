"""Content checks for the "multiplication" bonus practice levels
(category_level 2-20 currently): unedited starter code must not already
satisfy the challenge, and the intended solution must. Split out from the
old combined test_bonus_levels.py/test_bonus_levels_extended.py so each
category can be extended independently."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

BONUS_SOLUTIONS = {
    "lesson_25": "print(8 * 7)",
    "lesson_26": "print(2 * 3 * 4)",
    "lesson_99": "print(1.5 * 3)",
    "lesson_100": "print(8 * -4)",
    "lesson_101": "print(2 * 2 * 3 * 3)",
    "lesson_102": "print(round(4.2 * 1.5))",
    "lesson_103": "print(abs(-6 * 5))",
    "lesson_104": "print(3 * 3 > 10)",
    "lesson_105": "print(47 * 0)",
    "lesson_106": "print(3.5 * 2.5)",
    "lesson_107": "print(max(4 * 4, 3 * 6))",
    "lesson_108": 'print(int("9") * 4)',
    "lesson_109": "print(2 * 2 * 2 * 2 * 2)",
    "lesson_110": "print(5 * 5 == 20)",
    "lesson_111": "print(-7 * -6)",
    "lesson_112": "print(2.5 * 2 * 1.5)",
    "lesson_113": "print((2 * 5) ** 2)",
    "lesson_114": "print(2 * 3 * 2 * 1 * 2)",
    "lesson_115": "print(round(1.5 * 2), 4 * 4 > 20)",
    "lesson_560": "print((8 * 9) // 5)",
    "lesson_561": "print((9 * 7) % 5)",
    "lesson_562": "print((9 * 8) // 5, (9 * 8) % 5)",
    "lesson_563": "print(-1.5 * 4 * -2)",
    "lesson_564": "print(round(2.71828 * 3, 3))",
    "lesson_565": "print(6 * 6 >= 40)",
    "lesson_566": "print(6 * 6 <= 30)",
    "lesson_567": "print(4 * 5 + 10)",
    "lesson_568": "print(6 * 7 - 12)",
    "lesson_569": "print(3 * 4 + 5 * 6)",
    "lesson_570": "print((6 + 4) * 5)",
    "lesson_571": 'print(int("5") * 6 + 3)',
    "lesson_572": "print(2 * 5 ** 2)",
    "lesson_573": "print(max(3 * 3, 2 * 8, 5 * 5))",
    "lesson_574": "print(min(5 * 5, 3 * 8, 2 * 11))",
    "lesson_575": "print(round(-1.5 * 4 * -3))",
    "lesson_576": "print(4 * 5 + 2 > 3 * 8)",
    "lesson_577": 'print(int("7") * 3 + 2 == 25)',
    "lesson_578": "print((3 * 4 * 5) // 7, (3 * 4 * 5) % 7)",
    "lesson_579": "print(round(1.5 * 4, 1), (5 * 6) // 4, 3 * 4 + 1 > 2 * 5)",
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


def test_multiplication_category_has_a_full_1_to_40_level_progression(engine):
    lessons = engine.lessons_in_category("multiplication")
    assert len(lessons) == 40
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 41))
