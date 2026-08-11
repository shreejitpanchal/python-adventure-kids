"""Content + behavior checks for lessons 7-13 (variables through lists).

Same invariant as the arithmetic lessons: unedited starter code must NOT
already satisfy the challenge, and the intended solution must produce
exactly the expected output. Lesson 9 (input) is intentionally excluded --
its starter code is correct by design and is covered by test_input_lesson.py.
"""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

LESSON_SOLUTIONS = {
    "lesson_07": "age = 10\nprint(age)",
    "lesson_08": 'name = "Sam"\nprint(name)',
    "lesson_10": 'age = 5\nif age >= 8:\n    print("You can play!")\nelse:\n    print("You are too young!")',
    "lesson_11": 'for i in range(3):\n    print("Hooray!")',
    "lesson_12": 'def greet():\n    print("Howdy!")\n\ngreet()',
    "lesson_13": 'fruits = ["apple", "banana", "orange"]\nprint(fruits[1])',
}


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_chain_from_lesson_06_through_lesson_13(engine):
    ids = []
    current = engine.get("lesson_06")
    for _ in range(8):
        ids.append(current.id)
        nxt = engine.next_after(current.id)
        if nxt is None:
            break
        current = nxt
    assert ids == [
        "lesson_06", "lesson_07", "lesson_08", "lesson_09", "lesson_10",
        "lesson_11", "lesson_12", "lesson_13",
    ]


def test_lesson_09_awards_python_explorer_badge(engine):
    assert engine.get("lesson_09").badge == "python_explorer"


def test_lesson_11_awards_loop_wizard_badge(engine):
    assert engine.get("lesson_11").badge == "loop_wizard"


@pytest.mark.parametrize("lesson_id", list(LESSON_SOLUTIONS))
def test_unedited_starter_code_does_not_satisfy_the_challenge(engine, lesson_id):
    lesson = engine.get(lesson_id)
    result = run_code(lesson.starter_code.strip())
    assert result.success is True, f"{lesson_id} starter code failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is False, (
        f"{lesson_id}'s starter code already satisfies the challenge without editing"
    )


@pytest.mark.parametrize("lesson_id,solution", LESSON_SOLUTIONS.items())
def test_intended_solution_satisfies_the_challenge(engine, lesson_id, solution):
    lesson = engine.get(lesson_id)
    result = run_code(solution)
    assert result.success is True, f"{lesson_id} solution failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is True, (
        f"{lesson_id}'s intended solution produced {result.stdout!r}, expected {lesson.expected_output!r}"
    )
