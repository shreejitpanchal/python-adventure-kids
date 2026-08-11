"""Content + behavior checks for the arithmetic lessons (2-6): each challenge must
require an actual edit (the unedited starter code must NOT already satisfy it),
and the intended solution must produce exactly the expected output.
"""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

LESSON_SOLUTIONS = {
    "lesson_02": 'print(7)',
    "lesson_03": 'print(7 + 5)',
    "lesson_04": 'print(9 - 4)',
    "lesson_05": 'print(5 * 6)',
    "lesson_06": 'print(20 / 4)',
}


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_chain_from_lesson_01_through_lesson_06(engine):
    ids = []
    current = engine.get("lesson_01")
    for _ in range(6):
        ids.append(current.id)
        nxt = engine.next_after(current.id)
        if nxt is None:
            break
        current = nxt
    assert ids == ["lesson_01", "lesson_02", "lesson_03", "lesson_04", "lesson_05", "lesson_06"]


def test_lesson_06_awards_math_master_badge(engine):
    assert engine.get("lesson_06").badge == "math_master"


@pytest.mark.parametrize("lesson_id", list(LESSON_SOLUTIONS))
def test_unedited_starter_code_does_not_satisfy_the_challenge(engine, lesson_id):
    lesson = engine.get(lesson_id)
    result = run_code(lesson.starter_code.strip())
    assert result.success is True
    assert validate_output(result.stdout, lesson.expected_output) is False, (
        f"{lesson_id}'s starter code already satisfies the challenge without editing"
    )


@pytest.mark.parametrize("lesson_id,solution", LESSON_SOLUTIONS.items())
def test_intended_solution_satisfies_the_challenge(engine, lesson_id, solution):
    lesson = engine.get(lesson_id)
    result = run_code(solution)
    assert result.success is True
    assert validate_output(result.stdout, lesson.expected_output) is True, (
        f"{lesson_id}'s intended solution {solution!r} produced {result.stdout!r}, "
        f"expected {lesson.expected_output!r}"
    )
