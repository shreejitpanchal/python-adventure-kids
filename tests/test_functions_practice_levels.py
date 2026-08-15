"""Content checks for the extended functions bonus practice levels
(category_level 2-20, lesson_380-lesson_398): same edit-required invariant
as test_bonus_levels_extended.py -- unedited starter code must not already
satisfy the challenge, and the intended solution must."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

SOLUTIONS = {
    "lesson_380": 'def greet(name):\n    print("Hi " + name + "!")\n\ngreet("Nova")',
    "lesson_381": (
        'def introduce(name, age):\n'
        '    print(name + " is " + str(age) + " years old.")\n\n'
        'introduce("Mia", 12)'
    ),
    "lesson_382": "def add_five(x):\n    return x + 5\n\nresult = add_five(20)\nprint(result)",
    "lesson_383": (
        "def double(n):\n    return n * 2\n\n"
        'answer = double(9)\nprint("Doubled:", answer)'
    ),
    "lesson_384": (
        'def greet(name="friend"):\n    print("Hello, " + name + "!")\n\n'
        'greet("Kai")'
    ),
    "lesson_385": (
        "def square(n):\n    return n * n\n\n"
        "def show_square(n):\n    result = square(n)\n    print(\"Square:\", result)\n\n"
        "show_square(6)"
    ),
    "lesson_386": (
        "def count_up(n):\n    for i in range(1, n + 1):\n        print(i)\n\n"
        "count_up(5)"
    ),
    "lesson_387": (
        "def check_temp(temp):\n"
        "    if temp > 30:\n"
        "        print(\"It's hot!\")\n"
        "    else:\n"
        "        print(\"It's not too hot.\")\n\n"
        "check_temp(35)"
    ),
    "lesson_388": (
        "def grade(score):\n"
        '    if score >= 50:\n        return "Pass"\n'
        '    else:\n        return "Fail"\n\n'
        "print(grade(75))"
    ),
    "lesson_389": "def area(width, height):\n    return width * height\n\nprint(area(6, 7))",
    "lesson_390": (
        'def welcome(place):\n    return "Welcome to " + place + "!"\n\n'
        'print(welcome("the Jungle"))'
    ),
    "lesson_391": (
        "def perimeter(width, height):\n    return 2 * (width + height)\n\n"
        "print(perimeter(10, 6))"
    ),
    "lesson_392": (
        "def triple(n):\n    return n * 3\n\n"
        "print(triple(2))\nprint(triple(5))\nprint(triple(10))"
    ),
    "lesson_393": (
        "def half(n):\n    return n / 2\n\n"
        "result = half(50)\ntotal = result + 100\nprint(total)"
    ),
    "lesson_394": (
        "def sum_to(n):\n    total = 0\n    for i in range(1, n + 1):\n"
        "        total += i\n    return total\n\nprint(sum_to(10))"
    ),
    "lesson_395": (
        'def repeat_word(word, times):\n    result = ""\n    for i in range(times):\n'
        '        result += word + " "\n    return result\n\n'
        'print(repeat_word("Hop", 4))'
    ),
    "lesson_396": (
        "def even_or_odd(n):\n"
        '    if n % 2 == 0:\n        return "even"\n'
        '    else:\n        return "odd"\n\n'
        "print(even_or_odd(7))"
    ),
    "lesson_397": (
        'def count_vowels(word):\n    count = 0\n    for letter in word:\n'
        '        if letter in "aeiouAEIOU":\n            count += 1\n    return count\n\n'
        'print(count_vowels("adventure"))'
    ),
    "lesson_398": (
        "def total_cost(price, quantity, discount):\n"
        "    subtotal = price * quantity\n"
        "    if subtotal > 50:\n        subtotal -= discount\n"
        "    return subtotal\n\n"
        "print(total_cost(10, 3, 5))\n"
        "print(total_cost(4, 2, 5))\n"
        "print(total_cost(20, 4, 15))"
    ),
}


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


@pytest.mark.parametrize("lesson_id,solution", SOLUTIONS.items())
def test_intended_solution_satisfies_the_challenge(engine, lesson_id, solution):
    lesson = engine.get(lesson_id)
    result = run_code(solution)
    assert result.success is True, f"{lesson_id} solution failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is True, (
        f"{lesson_id}'s intended solution produced {result.stdout!r}, expected {lesson.expected_output!r}"
    )


@pytest.mark.parametrize("lesson_id", list(SOLUTIONS))
def test_unedited_starter_code_does_not_satisfy_the_challenge(engine, lesson_id):
    lesson = engine.get(lesson_id)
    result = run_code(lesson.starter_code.strip())
    assert result.success is True, f"{lesson_id} starter code failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is False, (
        f"{lesson_id}'s starter code already satisfies the challenge without editing"
    )


@pytest.mark.parametrize("lesson_id", list(SOLUTIONS))
def test_bonus_level_is_marked_correctly(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert lesson.main_path is False
    assert lesson.badge is None
    assert lesson.next_lesson_id is None
    assert lesson.category == "functions"
    assert lesson.category_level >= 2


def test_functions_category_has_a_full_1_to_20_level_progression(engine):
    lessons = engine.lessons_in_category("functions")
    assert len(lessons) == 20
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 21))
    ids = {lesson.id for lesson in lessons}
    assert ids == {"lesson_12"} | set(SOLUTIONS)
