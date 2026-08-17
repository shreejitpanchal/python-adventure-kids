"""Content checks for the lists bonus practice levels (category_level 2-40,
lesson_400-lesson_418 and lesson_720-lesson_739) that bring the lists
category to a full 40-level progression alongside the pre-existing lesson_13
(category_level 1). Same shape as test_bonus_levels_extended.py: hand-written
solutions run through the real subprocess sandbox and checked against each
lesson's real expected_output."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

SOLUTIONS = {
    "lesson_400": 'fruits = ["apple", "banana", "orange"]\nprint(fruits[2])',
    "lesson_401": 'snacks = ["chips", "pretzels", "popcorn"]\nprint(snacks[-1])',
    "lesson_402": 'toys = ["robot", "ball", "kite", "yo-yo"]\nprint(len(toys))',
    "lesson_403": 'pets = ["cat", "dog"]\npets.append("fish")\nprint(pets)',
    "lesson_404": 'colors = ["red", "green", "blue"]\nfor color in colors:\n    print(color)',
    "lesson_405": 'letters = ["a", "b", "c"]\nfor i in range(len(letters)):\n    print(i, letters[i])',
    "lesson_406": "numbers = [4, 8, 15]\ntotal = 0\nfor n in numbers:\n    total += n\nprint(total)",
    "lesson_407": (
        "scores = [12, 45, 7, 39]\n"
        "biggest = scores[0]\n"
        "for s in scores:\n"
        "    if s > biggest:\n"
        "        biggest = s\n"
        "print(biggest)"
    ),
    "lesson_408": 'fruits = ["apple", "banana", "orange", "grape"]\nprint(fruits[0:2])',
    "lesson_409": 'fruits = ["apple", "banana", "orange"]\nfruits.remove("apple")\nprint(fruits)',
    "lesson_410": 'fruits = ["apple", "banana", "orange"]\nprint(", ".join(fruits))',
    "lesson_411": "numbers = [9, 3, 7, 1]\nprint(sorted(numbers))",
    "lesson_412": 'letters = ["a", "b", "a", "c", "a"]\nprint(letters.count("a"))',
    "lesson_413": (
        'fruits = ["apple", "banana", "orange"]\n'
        'if "banana" in fruits:\n'
        '    print("Found it!")\n'
        "else:\n"
        '    print("Not found.")'
    ),
    "lesson_414": "grades = [80, 90, 100, 70]\naverage = sum(grades) / len(grades)\nprint(average)",
    "lesson_415": "squares = []\nfor n in range(1, 5):\n    squares.append(n * n)\nprint(squares)",
    "lesson_416": (
        "def total_of(numbers):\n"
        "    return sum(numbers)\n"
        "\n"
        "prices = [3, 5, 10]\n"
        "print(total_of(prices))"
    ),
    "lesson_417": (
        "numbers = [1, 2, 3, 4, 5, 6, 7, 8]\n"
        "evens = []\n"
        "for n in numbers:\n"
        "    if n % 2 == 0:\n"
        "        evens.append(n)\n"
        "print(evens)"
    ),
    "lesson_418": (
        "multiples = []\n"
        "for n in range(1, 11):\n"
        "    if n % 3 == 0:\n"
        "        multiples.append(n)\n"
        "print(multiples)\n"
        "print(len(multiples))"
    ),
    "lesson_720": 'numbers = [5, 2, 8, 1, 9]\nnumbers.sort()\nprint(numbers)',
    "lesson_721": (
        'fruits = ["cat", "dog", "fish", "bird"]\n'
        "last = fruits.pop()\nprint(last)\nprint(fruits)"
    ),
    "lesson_722": (
        'fruits = ["apple", "banana", "orange"]\n'
        "removed = fruits.pop(1)\nprint(removed)\nprint(fruits)"
    ),
    "lesson_723": 'colors = ["red", "green", "blue"]\ncolors.insert(2, "purple")\nprint(colors)',
    "lesson_724": 'fruits = ["apple", "banana", "orange", "grape", "kiwi"]\nprint(fruits[2:])',
    "lesson_725": "numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]\nprint(numbers[1::2])",
    "lesson_726": 'letters = ["p", "y", "t", "h", "o", "n"]\nprint(letters[::-1])',
    "lesson_727": "grid = [[1, 2], [3, 4], [5, 6]]\nprint(grid[2][1])",
    "lesson_728": "grid = [[7, 8], [9, 10], [11, 12]]\nfor row in grid:\n    print(row)",
    "lesson_729": (
        "grid = [[5, 6, 7], [8, 9, 10]]\n"
        "for row in grid:\n    for value in row:\n        print(value)"
    ),
    "lesson_730": (
        'fruits = ["cat", "dog", "bird", "fish"]\n'
        "for index, fruit in enumerate(fruits):\n    print(index, fruit)"
    ),
    "lesson_731": (
        'tasks = ["pack bag", "tie shoes", "go to school", "say bye"]\n'
        "for number, task in enumerate(tasks, start=1):\n    print(number, task)"
    ),
    "lesson_732": "squares = [n * n for n in range(1, 8)]\nprint(squares)",
    "lesson_733": "evens = [n for n in range(1, 21) if n % 2 != 0]\nprint(evens)",
    "lesson_734": "scores = [88, 12, 56, 3, 71, 40]\nprint(min(scores))\nprint(max(scores))",
    "lesson_735": (
        "def squares_up_to(n):\n    return [i * i for i in range(1, n + 1)]\n\n"
        "print(squares_up_to(7))"
    ),
    "lesson_736": (
        "grid = [[10, 20], [30, 40], [50, 60]]\ntotal = 0\n"
        "for row in grid:\n    for value in row:\n        total += value\nprint(total)"
    ),
    "lesson_737": (
        "scores = [70, 95, 60, 85, 100, 55, 90]\nscores.sort()\n"
        "top_three = scores[-3:]\nprint(top_three)"
    ),
    "lesson_738": (
        "def top_scores(scores, cutoff):\n    passing = [s for s in scores if s >= cutoff]\n"
        "    return sorted(passing)\n\n"
        "print(top_scores([88, 45, 72, 90, 33, 67], 50))"
    ),
    "lesson_739": (
        "def class_average(students):\n    total = 0\n    count = 0\n"
        "    for name, scores in students:\n        for s in scores:\n"
        "            total += s\n            count += 1\n    return total / count\n\n"
        'students = [("Ana", [80, 90]), ("Ben", [70, 60, 100]), ("Cara", [90, 90, 90, 90, 90])]\n'
        "print(class_average(students))"
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
def test_bonus_level_is_marked_correctly(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert lesson.main_path is False
    assert lesson.next_lesson_id is None
    assert lesson.badge is None


def test_lists_category_has_a_full_1_to_40_level_progression():
    engine = LessonEngine()
    lessons = engine.lessons_in_category("lists")
    assert len(lessons) == 40
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 41))
