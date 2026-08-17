"""Content checks for the "variables" bonus practice levels (category_level
2-20 currently): unedited starter code must not already satisfy the
challenge, and the intended solution must. Split out from the old combined
test_bonus_levels_extended.py so each category can be extended
independently."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

BONUS_SOLUTIONS = {
    "lesson_29": "score = 5\nscore = 20\nprint(score)",
    "lesson_30": "a = 7\nb = 9\nprint(a, b)",
    "lesson_31": "price = 12\nprint(price + 3)",
    "lesson_32": "coins = 20\ncoins = coins + 7\nprint(coins)",
    "lesson_33": "lives = 3\nlives += 4\nprint(lives)",
    "lesson_34": "health = 100\nhealth -= 35\nprint(health)",
    "lesson_35": "points = 6\npoints *= 5\nprint(points)",
    "lesson_36": 'name = "Explorer"\nprint(name)',
    "lesson_37": 'name = "Ana"\nage = 11\nprint(name, age)',
    "lesson_38": "a = 5\nb = 9\ntemp = a\na = b\nb = temp\nprint(a, b)",
    "lesson_39": "is_small = 4 < 2\nprint(is_small)",
    "lesson_40": "smallest = min(15, 6)\nprint(smallest)",
    "lesson_41": "a = 10\nb = 20\nc = 30\nprint(a + b + c)",
    "lesson_42": "x = 7\nprint(x * x)",
    "lesson_43": 'word = "Snake"\nword = word + "!"\nprint(word)',
    "lesson_44": "weight = 12.3\nprint(round(weight))",
    "lesson_45": "change = -18\nprint(abs(change))",
    "lesson_46": "total = 10\ntotal = total + 5\ntotal = total + 5\nprint(total)",
    "lesson_47": 'hero = "Champion"\npoints = 0\npoints += 20\npoints += 30\nprint(hero, points)',
    "lesson_600": "weight = 12\nprint(f\"Weight: {weight}\")",
    "lesson_601": "name = \"Ana\"\nage = 11\nprint(f\"{name} is {age}\")",
    "lesson_602": "price = 12\nprint(f\"Total: {price + 3}\")",
    "lesson_603": "coins = 50\ncoins //= 7\nprint(coins)",
    "lesson_604": "coins = 50\ncoins %= 7\nprint(coins)",
    "lesson_605": "power = 2\npower **= 4\nprint(power)",
    "lesson_606": "total = 4\ntotal += 6\ntotal *= 3\ntotal -= 5\nprint(total)",
    "lesson_607": "a = 5 > 8\nb = 6 > 2\nprint(a and b)",
    "lesson_608": "a = 2 > 9\nb = 7 > 10\nprint(a or b)",
    "lesson_609": "coins = 20\ncoins *= 3\nprint(f\"Coins: {coins}\")",
    "lesson_610": "name = \"Ana\"\nscore = 20\nscore += 15\nprint(f\"{name} scored {score}\")",
    "lesson_611": "e = 2.71828\nprint(round(e, 3))",
    "lesson_612": "a = 6\nb = 15\ntemp = a\na = b\nb = temp\nprint(f\"a={a}, b={b}\")",
    "lesson_613": "a = 15\nb = 6\nc = 20\nsmallest = min(a, b, c)\nprint(smallest)",
    "lesson_614": "price = 12\ntax = 3\ndiscount = 2\ntotal = price + tax - discount\nprint(f\"Total: {total}\")",
    "lesson_615": "age = 6\nheight = 125\ncan_ride = age >= 8 and height >= 130\nprint(can_ride)",
    "lesson_616": "stash = 8\nstash += 16\nstash //= 4\nprint(stash)",
    "lesson_617": "distance = 12.345\nprint(f\"Distance: {round(distance, 1)} miles\")",
    "lesson_618": "score = 45\npassed = score >= 60\nprint(f\"Passed: {passed}\")",
    "lesson_619": "item = \"Toy\"\nprice = 8\nprice += 4\nqty = 3\ntotal = price * qty\ntotal -= 6\nin_stock = qty > 0 and total > 0\nprint(f\"{item}: {total} (in stock: {in_stock})\")",
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


def test_variables_category_has_a_full_1_to_40_level_progression(engine):
    lessons = engine.lessons_in_category("variables")
    assert len(lessons) == 40
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 41))
