"""Content checks for the bonus practice levels (numbers/addition/subtraction/
multiplication/division, levels 2-3): same edit-required invariant as the
main-path arithmetic lessons -- unedited starter code must not already
satisfy the challenge, and the intended solution must."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

BONUS_SOLUTIONS = {
    "lesson_19": "print(42)",
    "lesson_20": "print(100)",
    "lesson_21": "print(15 + 27)",
    "lesson_22": "print(4 + 6 + 9)",
    "lesson_23": "print(50 - 18)",
    "lesson_24": "print(30 - 12 - 5)",
    "lesson_25": "print(8 * 7)",
    "lesson_26": "print(2 * 3 * 4)",
    "lesson_27": "print(36 / 6)",
    "lesson_28": "print(42 / 6)",
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
