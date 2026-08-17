"""Content checks for the new Strings bonus practice levels (category_level
2-20, lessons lesson_300..lesson_318): the strings category now has a full
1-20 progression, the new levels are all properly marked as bonus levels,
and the intended solution to each challenge actually produces the output
the lesson expects when run through the real sandbox -- mirroring the
pattern used for the other categories' bonus levels in
tests/test_bonus_levels_extended.py."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.inprocess_runner import run_code

NEW_STRINGS_IDS = [f"lesson_{300 + n}" for n in range(19)] + [
    f"lesson_{620 + n}" for n in range(20)
]  # lesson_300..lesson_318, lesson_620..lesson_639

# The intended solution for each challenge -- what a child's edited
# starter_code should look like once the level is solved.
SOLUTIONS = {
    "lesson_300": 'first = "Sun"\nsecond = "flower"\nprint(first + second)',
    "lesson_301": 'part1 = "Fire"\npart2 = "fly"\npart3 = "!"\nprint(part1 + part2 + part3)',
    "lesson_302": 'word = "unicorn"\nprint(len(word))',
    "lesson_303": 'shout = "whisper"\nprint(shout.upper())',
    "lesson_304": 'loud = "SHOUTING"\nprint(loud.lower())',
    "lesson_305": 'points = 7\nprint("Points: " + str(points))',
    "lesson_306": 'laugh = "ho"\nprint(laugh * 4)',
    "lesson_307": 'word = "galaxy"\nprint(word[0])',
    "lesson_308": 'word = "rocket"\nprint(word[-1])',
    "lesson_309": 'word = "dinosaur"\nprint(word[0:4])',
    "lesson_310": 'messy = "   space   "\nprint(messy.strip())',
    "lesson_311": 'sentence = "I like apples"\nprint(sentence.replace("apples", "grapes"))',
    "lesson_312": 'word = "mississippi"\nprint(word.count("s"))',
    "lesson_313": 'name = "Nova"\nprint(f"Hi {name}")',
    "lesson_314": 'a = 7\nb = 6\nprint(f"{a} + {b} = {a + b}")',
    "lesson_315": 'word = "sunshine"\nprint(word.startswith("sun"))\nprint(word.endswith("rise"))',
    "lesson_316": 'phrase = "the lost city"\nprint(phrase.title())',
    "lesson_317": 'raw = "   quiet please   "\nprint(raw.strip().upper())',
    "lesson_318": 'name = "Explorer"\nprint(f"{name.upper()} has {len(name)} letters")',
    "lesson_620": 'sentence = "I like dogs"\nprint(sentence.split())',
    "lesson_621": 'sentence = "The big yellow sun is warm"\nprint(len(sentence.split()))',
    "lesson_622": 'colors = "pink,purple,gold"\nprint(colors.split(","))',
    "lesson_623": 'crew = ["Sam", "Max", "Ivy"]\nprint("-".join(crew))',
    "lesson_624": 'word = "backpack"\nprint(word.find("pack"))',
    "lesson_625": 'code = "77042"\nprint(code.isdigit())\nprint(code.isalpha())',
    "lesson_626": 'word = "roadtrip"\nprint(word[::2])',
    "lesson_627": 'word = "level"\nprint(word[::-1])',
    "lesson_628": 'password = "python"\nguess = "python"\nprint(password == guess)',
    "lesson_629": 'title = "GO"\nprint(title.center(8, "-"))',
    "lesson_630": 'num = "42"\nprint(num.zfill(5))',
    "lesson_631": 'a = 3\nb = 4\nc = 5\nprint(f"{a}-{b}-{c} sum={a + b + c}")',
    "lesson_632": 'text = "banana"\nprint(text.replace("a", "4").replace("e", "3"))',
    "lesson_633": 'sentence = "See you later alligator"\nprint(sentence.split()[-1])',
    "lesson_634": 'fruit = "pineapple"\nprint("apple" in fruit)',
    "lesson_635": 'sentence = "Python is super duper fun"\nprint(f"That sentence has {len(sentence.split())} words")',
    "lesson_636": 'print("=" * 6 + ">")',
    "lesson_637": 'raw = "  GOOD MORNING SUNSHINE  "\nprint(raw.strip().lower().title())',
    "lesson_638": 'sentence = "welcome to the jungle"\nprint(sentence.split()[0].upper())',
    "lesson_639": (
        'sentence = "the lost city of gold"\n'
        "words = sentence.split()\n"
        'print(f"The sentence has {len(words)} words and the first word is {words[0].upper()}")'
    ),
}


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_strings_category_has_a_full_1_to_40_level_progression(engine):
    lessons = engine.lessons_in_category("strings")
    assert len(lessons) == 40
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 41))


@pytest.mark.parametrize("lesson_id", NEW_STRINGS_IDS)
def test_new_lesson_is_marked_as_a_bonus_level(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert lesson.main_path is False
    assert lesson.badge is None
    assert lesson.next_lesson_id is None
    assert lesson.category == "strings"
    assert lesson.category_level >= 2


@pytest.mark.parametrize("lesson_id", NEW_STRINGS_IDS)
def test_unedited_starter_code_does_not_satisfy_the_challenge(engine, lesson_id):
    lesson = engine.get(lesson_id)
    result = run_code(lesson.starter_code.strip())
    assert result.success is True, f"{lesson_id} starter code failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is False, (
        f"{lesson_id}'s starter code already satisfies the challenge without editing"
    )


@pytest.mark.parametrize("lesson_id,solution", SOLUTIONS.items())
def test_intended_solution_satisfies_the_challenge(engine, lesson_id, solution):
    lesson = engine.get(lesson_id)
    result = run_code(solution)
    assert result.success is True, f"{lesson_id} solution failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is True, (
        f"{lesson_id}'s intended solution produced {result.stdout!r}, expected {lesson.expected_output!r}"
    )


def test_all_39_new_lesson_ids_are_covered_by_the_solutions_map():
    assert set(SOLUTIONS.keys()) == set(NEW_STRINGS_IDS)
