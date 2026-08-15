"""Content checks for the extended bonus practice levels added across
variables/numbers/addition/subtraction/multiplication/division (variables
levels 2-20, the other five categories' levels 4-20): same edit-required
invariant as test_bonus_levels.py -- unedited starter code must not already
satisfy the challenge, and the intended solution must."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

BONUS_SOLUTIONS = {
    # -- variables (category_level 2-20) --------------------------------
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
    # -- numbers (category_level 4-20) -----------------------------------
    "lesson_48": "print(-12)",
    "lesson_49": "print(4.25)",
    "lesson_50": "print(8, 20)",
    "lesson_51": "print(abs(-14))",
    "lesson_52": "print(round(4.2))",
    "lesson_53": "print(3 > 10)",
    "lesson_54": "print(5 == 9)",
    "lesson_55": "print(10 != 10)",
    "lesson_56": "print(max(23, 17))",
    "lesson_57": "print(min(31, 19))",
    "lesson_58": "print(3 ** 4)",
    "lesson_59": 'print(int("15") + 5)',
    "lesson_60": "print(round(-8.6))",
    "lesson_61": "print(abs(-12.25))",
    "lesson_62": "print((-3) ** 2)",
    "lesson_63": "print(9 - 6 > 10)",
    "lesson_64": "print(round(17.4), max(6, 21), abs(-30))",
    # -- addition (category_level 4-20) -----------------------------------
    "lesson_65": "print(3.5 + 2.25)",
    "lesson_66": "print(15 + -6)",
    "lesson_67": "print(6 + 7 + 8 + 9)",
    "lesson_68": "print(round(5.6 + 3.1))",
    "lesson_69": "print(abs(-20 + 6))",
    "lesson_70": "print(4 + 3 > 10)",
    "lesson_71": "print(2 + 2 + 2 + 2 + 2)",
    "lesson_72": "print(4.75 + 1.5)",
    "lesson_73": "print(max(4 + 4, 2 + 9))",
    "lesson_74": 'print(int("20") + 8)',
    "lesson_75": "print(10 + 20 + 30 + 40 + 50)",
    "lesson_76": "print(6 + 6 == 11)",
    "lesson_77": "print(-9 + -14)",
    "lesson_78": "print(2.5 + 4.5 + 1.5)",
    "lesson_79": "print((4 + 6) ** 2)",
    "lesson_80": "print(5 + 10 + 15 + 20 + 25 + 30)",
    "lesson_81": "print(round(4.5 + 1.5), 8 + 8 > 20)",
    # -- subtraction (category_level 4-20) --------------------------------
    "lesson_82": "print(6.75 - 2.5)",
    "lesson_83": "print(15 - -6)",
    "lesson_84": "print(50 - 5 - 10 - 15)",
    "lesson_85": "print(round(12.7 - 4.3))",
    "lesson_86": "print(abs(6 - 25))",
    "lesson_87": "print(9 - 8 > 5)",
    "lesson_88": "print(100 - 20 - 20 - 20 - 20 - 20)",
    "lesson_89": "print(9.5 - 2.25)",
    "lesson_90": "print(min(20 - 5, 15 - 2))",
    "lesson_91": 'print(int("30") - 12)',
    "lesson_92": "print(200 - 10 - 20 - 30 - 40 - 50)",
    "lesson_93": "print(15 - 5 == 11)",
    "lesson_94": "print(-20 - -8)",
    "lesson_95": "print(30.5 - 8.25 - 4.5)",
    "lesson_96": "print((15 - 7) ** 2)",
    "lesson_97": "print(100 - 5 - 10 - 15 - 20 - 25)",
    "lesson_98": "print(round(12.5 - 4.5), 30 - 25 > 10)",
    # -- multiplication (category_level 4-20) ------------------------------
    "lesson_99": "print(1.5 * 3)",
    "lesson_100": "print(8 * -4)",
    "lesson_101": "print(2 * 2 * 3 * 3)",
    "lesson_102": "print(round(4.2 * 1.5))",
    "lesson_103": "print(abs(-6 * 5))",
    "lesson_104": "print(3 * 3 > 10)",
    "lesson_105": "print(47 * 0)",
    "lesson_106": "print(3.5 * 2.5)",
    "lesson_107": "print(max(4 * 4, 3 * 6))",
    "lesson_108": 'print(int("9") * 4)',
    "lesson_109": "print(2 * 2 * 2 * 2 * 2)",
    "lesson_110": "print(5 * 5 == 20)",
    "lesson_111": "print(-7 * -6)",
    "lesson_112": "print(2.5 * 2 * 1.5)",
    "lesson_113": "print((2 * 5) ** 2)",
    "lesson_114": "print(2 * 3 * 2 * 1 * 2)",
    "lesson_115": "print(round(1.5 * 2), 4 * 4 > 20)",
    # -- division (category_level 4-20) -------------------------------------
    "lesson_116": "print(9.5 / 2)",
    "lesson_117": "print(30 / -5)",
    "lesson_118": "print(240 / 4 / 3)",
    "lesson_119": "print(round(22 / 6))",
    "lesson_120": "print(abs(-36 / 4))",
    "lesson_121": "print(15 / 5 > 4)",
    "lesson_122": "print(23 // 5)",
    "lesson_123": "print(23 % 5)",
    "lesson_124": "print(27 // 5, 27 % 5)",
    "lesson_125": 'print(int("30") / 5)',
    "lesson_126": "print(min(42 / 6, 30 / 3))",
    "lesson_127": "print(15 / 3 == 6)",
    "lesson_128": "print(-42 / -6)",
    "lesson_129": "print(90 / 3 / 2)",
    "lesson_130": "print((30 / 5) ** 2)",
    "lesson_131": "print(100 // 9, 100 % 9)",
    "lesson_132": "print(round(25 / 4), 12 / 4 > 5)",
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


def test_every_new_lesson_has_a_unique_level_and_id():
    engine = LessonEngine()
    all_lessons = engine.all_in_order()
    levels = [lesson.level for lesson in all_lessons]
    assert len(levels) == len(set(levels)), "Duplicate lesson levels found"
    ids = [lesson.id for lesson in all_lessons]
    assert len(ids) == len(set(ids)), "Duplicate lesson ids found"


@pytest.mark.parametrize(
    "category,expected_count",
    [
        ("variables", 20),
        ("numbers", 20),
        ("addition", 20),
        ("subtraction", 20),
        ("multiplication", 20),
        ("division", 20),
    ],
)
def test_category_has_a_full_1_to_20_level_progression(engine, category, expected_count):
    lessons = engine.lessons_in_category(category)
    assert len(lessons) == expected_count
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, expected_count + 1))
