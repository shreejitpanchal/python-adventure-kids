"""Content checks for the extended `input` category bonus practice levels
(category_level 2-20, lesson_320-lesson_338), bringing "Ask a Question" from
1 level to a full 20-level progression. Same shape as
test_bonus_levels_extended.py, but every lesson here uses input(), so
run_code needs stdin_text and validate_output needs input_value."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

# lesson_id -> (solved_code, test_input_value)
SOLUTIONS: dict[str, tuple[str, str]] = {
    "lesson_320": (
        'name = input("What is your name? ")\nprint("Hi " + name + ", you are AWESOME!")',
        "Maya",
    ),
    "lesson_321": (
        'n = int(input("Type a number: "))\nprint(n * 2)',
        "6",
    ),
    "lesson_322": (
        'n = int(input("Type a number: "))\nprint(n * n)',
        "5",
    ),
    "lesson_323": (
        'n = int(input("Type a number: "))\nprint(n + 10)',
        "8",
    ),
    "lesson_324": (
        'n = int(input("Type a number: "))\nprint(n * 3)',
        "4",
    ),
    "lesson_325": (
        'n = float(input("Type a number: "))\nprint(n / 2)',
        "10",
    ),
    "lesson_326": (
        'age = int(input("How old are you? "))\nprint(age + 1)',
        "9",
    ),
    "lesson_327": (
        'age = int(input("How old are you? "))\nprint(age + 10)',
        "9",
    ),
    "lesson_328": (
        'n = int(input("Type a number: "))\nprint(-n)',
        "7",
    ),
    "lesson_329": (
        'n = int(input("Type a number: "))\nprint(n % 3)',
        "10",
    ),
    "lesson_330": (
        'n = int(input("Type a number: "))\nprint(n // 5)',
        "23",
    ),
    "lesson_331": (
        'word = input("Type a word: ")\nprint(len(word))',
        "python",
    ),
    "lesson_332": (
        'word = input("Type a word: ")\nprint(word.upper())',
        "cat",
    ),
    "lesson_333": (
        'word = input("Type a word: ")\nprint(word + " World")',
        "Hello",
    ),
    "lesson_334": (
        'age = int(input("How old are you? "))\nprint("Explorer is " + str(age) + " years old!")',
        "9",
    ),
    "lesson_335": (
        'n = int(input("Type a number: "))\nprint((n + 10) / 2)',
        "20",
    ),
    "lesson_336": (
        'price = float(input("What is the price? "))\nprint(price * 2)',
        "5",
    ),
    "lesson_337": (
        'celsius = float(input("What is the temperature in Celsius? "))\nprint(celsius * 9 / 5 + 32)',
        "20",
    ),
    "lesson_338": (
        'n = int(input("Type a number: "))\nprint(n + 4)\nprint(n - 4)\nprint(n * 4)',
        "10",
    ),
}


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


@pytest.mark.parametrize("lesson_id,solution", SOLUTIONS.items())
def test_intended_solution_satisfies_the_challenge(engine, lesson_id, solution):
    code, value = solution
    result = run_code(code, stdin_text=f"{value}\n")
    assert result.success is True, f"{lesson_id} solution failed to run: {result.stderr}"
    lesson = engine.get(lesson_id)
    assert validate_output(result.stdout, lesson.expected_output, input_value=value) is True, (
        f"{lesson_id}'s intended solution produced {result.stdout!r} with input {value!r}, "
        f"expected {lesson.expected_output!r}"
    )


@pytest.mark.parametrize("lesson_id", list(SOLUTIONS))
def test_new_input_level_is_marked_correctly(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert lesson.main_path is False
    assert lesson.next_lesson_id is None
    assert lesson.badge is None
    assert lesson.input_prompt
    assert lesson.category_level >= 2


def test_input_category_has_a_full_1_to_20_level_progression():
    engine = LessonEngine()
    lessons = engine.lessons_in_category("input")
    assert len(lessons) == 20
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 21))
