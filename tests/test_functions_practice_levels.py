"""Content checks for the extended functions bonus practice levels
(category_level 2-40, lesson_380-lesson_398 and lesson_700-lesson_719): same
edit-required invariant as test_bonus_levels_extended.py -- unedited starter
code must not already satisfy the challenge, and the intended solution
must."""
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
    "lesson_700": "def average3(a, b, c):\n    return (a + b + c) / 3\n\nprint(average3(10, 20, 30))",
    "lesson_701": "def power(base, exponent=2):\n    return base ** exponent\n\nprint(power(2, 5))",
    "lesson_702": (
        'def split_name(full_name):\n    parts = full_name.split(" ")\n'
        "    return parts[0], parts[1]\n\n"
        'first, last = split_name("Grace Hopper")\nprint(first)\nprint(last)'
    ),
    "lesson_703": (
        "def divide(a, b):\n    quotient = a // b\n    remainder = a % b\n"
        "    return quotient, remainder\n\n"
        "q, r = divide(23, 4)\nprint(q)\nprint(r)"
    ),
    "lesson_704": (
        "def make_multiples(n, count):\n    result = []\n"
        "    for i in range(1, count + 1):\n        result.append(n * i)\n"
        "    return result\n\nprint(make_multiples(4, 6))"
    ),
    "lesson_705": (
        "def total(*args):\n    result = 0\n    for n in args:\n        result += n\n"
        "    return result\n\nprint(total(5, 10, 15, 20))"
    ),
    "lesson_706": (
        "def biggest(*args):\n    result = args[0]\n    for n in args:\n"
        "        if n > result:\n            result = n\n    return result\n\n"
        "print(biggest(15, 3, 22, 8, 11))"
    ),
    "lesson_707": (
        "def total(*args):\n    result = 0\n    for n in args:\n        result += n\n"
        "    return result\n\ndef average(*args):\n    return total(*args) / len(args)\n\n"
        "print(average(10, 20, 30, 40))"
    ),
    "lesson_708": (
        'def countdown(n):\n    if n <= 0:\n        print("Liftoff!")\n    else:\n'
        "        print(n)\n        countdown(n - 1)\n\ncountdown(5)"
    ),
    "lesson_709": (
        "def factorial(n):\n    if n <= 1:\n        return 1\n"
        "    return n * factorial(n - 1)\n\nprint(factorial(5))"
    ),
    "lesson_710": (
        "def sum_to(n):\n    if n <= 0:\n        return 0\n"
        "    return n + sum_to(n - 1)\n\nprint(sum_to(6))"
    ),
    "lesson_711": (
        "def min_and_max(numbers):\n    smallest = numbers[0]\n    largest = numbers[0]\n"
        "    for n in numbers:\n        if n < smallest:\n            smallest = n\n"
        "        if n > largest:\n            largest = n\n    return smallest, largest\n\n"
        "low, high = min_and_max([10, 3, 25, 1, 18])\nprint(high - low)"
    ),
    "lesson_712": (
        'def repeat_word(word, times=3):\n    result = ""\n    for i in range(times):\n'
        '        result += word + " "\n    return result.strip()\n\n'
        'print(repeat_word("Go", 5))'
    ),
    "lesson_713": (
        "def sum_evens(n):\n    if n <= 0:\n        return 0\n"
        "    if n % 2 == 0:\n        return n + sum_evens(n - 1)\n"
        "    else:\n        return sum_evens(n - 1)\n\nprint(sum_evens(10))"
    ),
    "lesson_714": (
        "def filter_above(numbers, threshold):\n    result = []\n    for n in numbers:\n"
        "        if n > threshold:\n            result.append(n)\n    return result\n\n"
        "print(filter_above([12, 4, 30, 7, 18], 10))"
    ),
    "lesson_715": (
        "def stats(*args):\n    total = 0\n    for n in args:\n        total += n\n"
        "    return total, total / len(args)\n\n"
        "def show_stats(*args):\n    s, avg = stats(*args)\n"
        '    print("Sum:", s)\n    print("Average:", avg)\n\nshow_stats(10, 20, 30)'
    ),
    "lesson_716": (
        "def power(base, exponent):\n    if exponent == 0:\n        return 1\n"
        "    return base * power(base, exponent - 1)\n\nprint(power(3, 4))"
    ),
    "lesson_717": (
        "def count_even_odd(numbers):\n    evens = 0\n    odds = 0\n    for n in numbers:\n"
        "        if n % 2 == 0:\n            evens += 1\n        else:\n            odds += 1\n"
        "    return evens, odds\n\n"
        "e, o = count_even_odd([10, 15, 20, 25, 30, 35, 40, 45])\n"
        'print("Evens:", e)\nprint("Odds:", o)'
    ),
    "lesson_718": (
        "def total_cost(price, quantity, discount=0, tax_rate=0.1):\n"
        "    subtotal = price * quantity - discount\n"
        "    total = subtotal + subtotal * tax_rate\n    return total\n\n"
        "print(total_cost(10, 5, 10))"
    ),
    "lesson_719": (
        "def order_summary(price, quantity, discount=0):\n"
        "    subtotal = price * quantity\n"
        "    if subtotal > 100:\n        subtotal -= discount\n"
        "    return subtotal, subtotal / quantity\n\n"
        "total1, unit1 = order_summary(10, 3)\nprint(total1, unit1)\n"
        "total2, unit2 = order_summary(20, 6, 15)\nprint(total2, unit2)\n"
        "total3, unit3 = order_summary(8, 20, 25)\nprint(total3, unit3)"
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


def test_functions_category_has_a_full_1_to_40_level_progression(engine):
    lessons = engine.lessons_in_category("functions")
    assert len(lessons) == 40
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 41))
    ids = {lesson.id for lesson in lessons}
    assert ids == {"lesson_12"} | set(SOLUTIONS)
