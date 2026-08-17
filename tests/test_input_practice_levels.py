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
    "lesson_640": (
        'n = int(input("Type a number: "))\nprint(round(n / 3, 1))',
        "7",
    ),
    "lesson_641": (
        'age = int(input("How old are you? "))\nprint(f"You are {age} years old!")',
        "9",
    ),
    "lesson_642": (
        'age = int(input("How old are you? "))\nprint(f"Next year you will be {age + 1}!")',
        "9",
    ),
    "lesson_643": (
        'word = input("Type a word: ")\nprint(word[::-1])',
        "otter",
    ),
    "lesson_644": (
        'word = input("Type a word: ")\nprint(word[0] + word[-1])',
        "python",
    ),
    "lesson_645": (
        'sentence = input("Type a short sentence: ")\nprint(len(sentence.split()))',
        "the cat sat down",
    ),
    "lesson_646": (
        'price = float(input("What is the price? "))\nprint(price - price * 0.1)',
        "20",
    ),
    "lesson_647": (
        'n = int(input("Type a number: "))\nprint(n // 3)\nprint(n % 3)',
        "17",
    ),
    "lesson_648": (
        'line = input("Type two numbers separated by a space: ")\n'
        "parts = line.split()\na = int(parts[0])\nb = int(parts[1])\nprint(a + b)",
        "4 7",
    ),
    "lesson_649": (
        'line = input("Type two numbers separated by a space: ")\n'
        "parts = line.split()\na = int(parts[0])\nb = int(parts[1])\nprint(a * b)",
        "3 6",
    ),
    "lesson_650": (
        'line = input("Type your first and last name separated by a space: ")\n'
        'parts = line.split()\nprint(f"Hello {parts[0]} {parts[1]}!")',
        "Maya Rivera",
    ),
    "lesson_651": (
        'line = input("Type the length and width separated by a space: ")\n'
        "parts = line.split()\nlength = int(parts[0])\nwidth = int(parts[1])\n"
        'print(f"Area: {length * width}")',
        "6 4",
    ),
    "lesson_652": (
        'text = input("Type a number: ")\nprint(text.isdigit())',
        "42",
    ),
    "lesson_653": (
        'word = input("Type a word: ")\nprint("a" in word)',
        "banana",
    ),
    "lesson_654": (
        'n = input("Type a number: ")\nprint(n.zfill(5))',
        "42",
    ),
    "lesson_655": (
        'celsius = float(input("What is the temperature in Celsius? "))\n'
        "fahrenheit = round(celsius * 9 / 5 + 32, 1)\n"
        'print(f"{celsius} C is {fahrenheit} F")',
        "25",
    ),
    "lesson_656": (
        'line = input("Type three numbers separated by spaces: ")\n'
        "parts = line.split()\na = int(parts[0])\nb = int(parts[1])\nc = int(parts[2])\n"
        "print(a + b + c)",
        "2 5 9",
    ),
    "lesson_657": (
        'sentence = input("Type a short sentence: ")\nprint(sentence.title())',
        "the lost city",
    ),
    "lesson_658": (
        'line = input("Type your first and last name separated by a space: ")\n'
        "parts = line.split()\nfirst = parts[0]\nlast = parts[1]\n"
        'print(f"{first.upper()} {last.upper()}")',
        "maya rivera",
    ),
    "lesson_659": (
        'line = input("Type your name and age separated by a space: ")\n'
        "parts = line.split()\nname = parts[0]\nage = int(parts[1])\n"
        'print(f"Hello {name.upper()}!")\nprint(f"Next year you will be {age + 1}.")',
        "nova 9",
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


def test_input_category_has_a_full_1_to_40_level_progression():
    engine = LessonEngine()
    lessons = engine.lessons_in_category("input")
    assert len(lessons) == 40
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 41))
