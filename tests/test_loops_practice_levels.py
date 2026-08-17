"""Content checks for the loops category's bonus practice levels (category_level
2-40, lesson_360 through lesson_378 and lesson_680 through lesson_699),
bringing loops up to a full 1-40 progression alongside the always-present
category_level-1 lesson_11. Same precedent as test_bonus_levels_extended.py: a
SOLUTIONS dict maps each lesson id to a hand-written solved-challenge code
string, verified against the lesson's real expected_output via
app.sandbox.runner.run_code + app.engine.validator.validate_output."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

# lesson_id -> (solution code, stdin_text or None)
SOLUTIONS = {
    "lesson_360": ("for i in range(3):\n    print(i)", None),
    "lesson_361": ("for i in range(5, 10):\n    print(i)", None),
    "lesson_362": ("for i in range(1, 10, 2):\n    print(i)", None),
    "lesson_363": ("for i in range(5, 0, -1):\n    print(i)", None),
    "lesson_364": ("total = 0\nfor i in range(1, 11):\n    total += i\nprint(total)", None),
    "lesson_365": ("total = 1\nfor i in range(1, 6):\n    total *= i\nprint(total)", None),
    "lesson_366": ("for i in range(1, 11):\n    if i % 2 != 0:\n        print(i)", None),
    "lesson_367": ('word = "code"\nfor ch in word:\n    print(ch)', None),
    "lesson_368": (
        'word = "banana"\ncount = 0\nfor ch in word:\n    if ch == "n":\n        count += 1\nprint(count)',
        None,
    ),
    "lesson_369": (
        'for i in range(1, 3):\n    row = ""\n    for j in range(1, 3):\n        if j > 1:\n'
        '            row = row + " "\n        row = row + str(i * j)\n    print(row)',
        None,
    ),
    "lesson_370": ("n = 1\nwhile n <= 8:\n    print(n)\n    n += 1", None),
    "lesson_371": ("n = 8\nwhile n >= 1:\n    print(n)\n    n -= 1", None),
    "lesson_372": ("n = 1\nwhile True:\n    print(n)\n    if n == 3:\n        break\n    n += 1", None),
    "lesson_373": ('result = ""\nfor i in range(1, 7):\n    result = result + str(i)\nprint(result)', None),
    "lesson_374": (
        'count = int(input("How many times? "))\nfor i in range(count):\n    print("Lap!")',
        "3\n",
    ),
    "lesson_375": ("product = 1\nfor i in range(1, 7):\n    product = product * i\nprint(product)", None),
    "lesson_376": (
        "total = 0\nfor i in range(1, 11):\n    if i % 2 != 0:\n        total += i\nprint(total)",
        None,
    ),
    "lesson_377": (
        'for row in range(1, 6):\n    line = ""\n    for col in range(row):\n        line = line + "*"\n    print(line)',
        None,
    ),
    "lesson_378": (
        "total = 0\nfor i in range(1, 21):\n    if i % 4 == 0:\n        total += i\nprint(total)",
        None,
    ),
    "lesson_680": ("for i in range(1, 8):\n    if i == 6:\n        continue\n    print(i)", None),
    "lesson_681": (
        "for i in range(1, 11):\n    if i % 3 == 0:\n        continue\n    print(i)",
        None,
    ),
    "lesson_682": (
        "n = 0\nwhile n < 8:\n    n += 1\n    if n == 3:\n        continue\n    print(n)",
        None,
    ),
    "lesson_683": (
        'for row in range(4):\n    line = ""\n    for col in range(3):\n        line = line + "*"\n    print(line)',
        None,
    ),
    "lesson_684": (
        'size = 4\nfor row in range(size):\n    line = ""\n    for col in range(size):\n'
        '        if row == 0 or row == size - 1 or col == 0 or col == size - 1:\n'
        '            line = line + "*"\n        else:\n            line = line + " "\n    print(line)',
        None,
    ),
    "lesson_685": ("for i in range(1, 50):\n    if i % 9 == 0:\n        print(i)\n        break", None),
    "lesson_686": (
        "for i in range(1, 100):\n    if i % 3 == 0 and i % 5 == 0:\n        print(i)\n        break",
        None,
    ),
    "lesson_687": ("n = 1\nwhile n < 100:\n    print(n)\n    n = n * 2", None),
    "lesson_688": ('word = "code"\nfor i in range(len(word) - 1, -1, -1):\n    print(word[i])', None),
    "lesson_689": (
        'word = "hello"\nreversed_word = ""\nfor i in range(len(word) - 1, -1, -1):\n'
        '    reversed_word = reversed_word + word[i]\nprint(reversed_word)',
        None,
    ),
    "lesson_690": (
        "for i in range(0, 2):\n    for j in range(0, 2):\n        for k in range(0, 2):\n            print(i, j, k)",
        None,
    ),
    "lesson_691": (
        "for i in range(1, 4):\n    for j in range(1, 4):\n        if i == j:\n            print(i, j)",
        None,
    ),
    "lesson_692": (
        "total = 0\nfor i in range(1, 5):\n    for j in range(1, 5):\n        total += i * j\nprint(total)",
        None,
    ),
    "lesson_693": (
        "total = 0\nfor i in range(1, 100):\n    total += i\n    if total > 50:\n        break\nprint(total)",
        None,
    ),
    "lesson_694": (
        'numbers = range(1, 9)\nresult = ""\nfor n in numbers:\n    if result != "":\n'
        '        result = result + ", "\n    result = result + str(n)\nprint(result)',
        None,
    ),
    "lesson_695": (
        'for i in range(1, 11):\n    if i % 4 == 0:\n        print("Fizz")\n    elif i % 5 == 0:\n'
        '        print("Buzz")\n    else:\n        print(i)',
        None,
    ),
    "lesson_696": (
        'for i in range(1, 16):\n    if i % 2 == 0 and i % 7 == 0:\n        print("FizzBuzz")\n'
        '    elif i % 2 == 0:\n        print("Fizz")\n    elif i % 7 == 0:\n        print("Buzz")\n'
        '    else:\n        print(i)',
        None,
    ),
    "lesson_697": (
        "product = 1\nn = 1\nwhile True:\n    product = product * n\n    if product > 500:\n"
        "        break\n    n += 1\nprint(product)\nprint(n)",
        None,
    ),
    "lesson_698": (
        "for i in range(1, 6):\n    for j in range(1, 6):\n        if i * j == 8:\n            print(i, j)\n            break",
        None,
    ),
    "lesson_699": (
        "total = 0\nfor i in range(1, 100):\n    if i % 7 == 0:\n        continue\n"
        "    if i % 3 == 0 or i % 5 == 0:\n        total += i\n    if total > 200:\n"
        "        break\nprint(total)\nprint(i)",
        None,
    ),
}


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


@pytest.mark.parametrize("lesson_id", list(SOLUTIONS))
def test_bonus_level_is_marked_correctly(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert lesson.main_path is False
    assert lesson.next_lesson_id is None
    assert lesson.badge is None


@pytest.mark.parametrize("lesson_id,solution", SOLUTIONS.items())
def test_intended_solution_satisfies_the_challenge(engine, lesson_id, solution):
    code, stdin_text = solution
    lesson = engine.get(lesson_id)
    result = run_code(code, stdin_text=stdin_text)
    assert result.success is True, f"{lesson_id} solution failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is True, (
        f"{lesson_id}'s intended solution produced {result.stdout!r}, expected {lesson.expected_output!r}"
    )


def test_loops_category_has_a_full_1_to_40_level_progression():
    engine = LessonEngine()
    lessons = engine.lessons_in_category("loops")
    assert len(lessons) == 40
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 41))
