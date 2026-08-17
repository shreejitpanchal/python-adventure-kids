"""Content checks for the "division" bonus practice levels (category_level
2-20 currently): unedited starter code must not already satisfy the
challenge, and the intended solution must. Split out from the old combined
test_bonus_levels.py/test_bonus_levels_extended.py so each category can be
extended independently."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

BONUS_SOLUTIONS = {
    "lesson_27": "print(36 / 6)",
    "lesson_28": "print(42 / 6)",
    "lesson_116": "print(9.5 / 2)",
    "lesson_117": "print(30 / -5)",
    "lesson_118": "print(240 / 4 / 3)",
    "lesson_119": "print(round(22 / 6))",
    "lesson_120": "print(abs(-36 / 4))",
    "lesson_121": "print(15 / 5 > 4)",
    "lesson_122": "print(23 // 5)",
    "lesson_123": "print(23 % 5)",
    "lesson_124": "print(27 // 5, 27 % 5)",
    "lesson_125": 'print(int("30") / 5)',
    "lesson_126": "print(min(42 / 6, 30 / 3))",
    "lesson_127": "print(15 / 3 == 6)",
    "lesson_128": "print(-42 / -6)",
    "lesson_129": "print(90 / 3 / 2)",
    "lesson_130": "print((30 / 5) ** 2)",
    "lesson_131": "print(100 // 9, 100 % 9)",
    "lesson_132": "print(round(25 / 4), 12 / 4 > 5)",
    "lesson_580": "print(23 / 5, 23 // 5)",
    "lesson_581": "print(23 / 5, 23 % 5)",
    "lesson_582": "print(23 / 5, 23 // 5, 23 % 5)",
    "lesson_583": "print(-15 / 5 / -1)",
    "lesson_584": "print(round(10 / 3, 3))",
    "lesson_585": "print(18 / 4 >= 5)",
    "lesson_586": "print(27 / 4 <= 6)",
    "lesson_587": "print(30 / 5 + 10)",
    "lesson_588": "print(40 / 8 - 3)",
    "lesson_589": "print(30 / 5 + 18 / 3)",
    "lesson_590": "print((18 + 6) / 4)",
    "lesson_591": 'print(int("30") / 5 + 2)',
    "lesson_592": "print(50 / 5 ** 2)",
    "lesson_593": "print(max(30 / 5, 42 / 6, 16 / 4))",
    "lesson_594": "print(min(42 / 6, 45 / 5, 18 / 3))",
    "lesson_595": "print(round(-17 / 6 / -1, 2))",
    "lesson_596": "print(30 / 5 + 2 > 24 / 3 + 1)",
    "lesson_597": 'print(int("30") / 5 + 3 == 10.0)',
    "lesson_598": "print((18 + 12) / 4, (18 + 12) // 4, (18 + 12) % 4)",
    "lesson_599": "print(round(17 / 5, 1), (24 + 6) // 5, 20 / 8 > 15 / 5)",
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


def test_division_category_has_a_full_1_to_40_level_progression(engine):
    lessons = engine.lessons_in_category("division")
    assert len(lessons) == 40
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 41))
