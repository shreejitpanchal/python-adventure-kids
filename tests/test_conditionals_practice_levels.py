"""Content checks for the extended bonus practice levels added to the
conditionals category (levels 2-20, lesson_340 through lesson_358): same
rigor as test_bonus_levels_extended.py -- run the hand-written solved
challenge through the real sandbox and confirm it actually satisfies each
lesson's expected_output."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

SOLUTIONS = {
    # -- conditionals (category_level 2-20) --------------------------------
    "lesson_340": (
        "score = 75\n"
        "if score >= 90:\n"
        '    print("Excellent!")\n'
        "elif score >= 70:\n"
        '    print("Good job!")\n'
        "else:\n"
        '    print("Keep practicing!")'
    ),
    "lesson_341": (
        "apples = 9\n"
        "oranges = 4\n"
        "if apples > oranges:\n"
        '    print("You have more apples!")\n'
        "else:\n"
        '    print("You have more oranges!")'
    ),
    "lesson_342": (
        "height = 120\n"
        "age = 8\n"
        "if height >= 120 and age >= 8:\n"
        '    print("You can ride the roller coaster!")\n'
        "else:\n"
        '    print("Not yet - you need to grow a bit more.")'
    ),
    "lesson_343": (
        'homework_done = "yes"\n'
        'chores_done = "no"\n'
        'if homework_done == "yes" or chores_done == "yes":\n'
        '    print("You can watch one show!")\n'
        "else:\n"
        '    print("Finish something first!")'
    ),
    "lesson_344": (
        "is_raining = False\n"
        "if not is_raining:\n"
        '    print("Let\'s play outside!")\n'
        "else:\n"
        '    print("Let\'s stay inside.")'
    ),
    "lesson_345": (
        'has_ticket = "yes"\n'
        "age = 12\n"
        'if has_ticket == "yes":\n'
        "    if age >= 12:\n"
        '        print("Enjoy the movie!")\n'
        "    else:\n"
        '        print("This movie needs an adult with you.")\n'
        "else:\n"
        '    print("You need a ticket first!")'
    ),
    "lesson_346": (
        'password = "secret123"\n'
        'if password == "secret123":\n'
        '    print("Access granted!")\n'
        "else:\n"
        '    print("Access denied.")'
    ),
    "lesson_347": (
        'age_text = "13"\n'
        "age = int(age_text)\n"
        "if age >= 13:\n"
        '    print("You are a teenager or older!")\n'
        "else:\n"
        '    print("You are still a kid!")'
    ),
    "lesson_348": (
        "score = 75\n"
        "if score >= 90:\n"
        '    print("Letter grade: A")\n'
        "elif score >= 80:\n"
        '    print("Letter grade: B")\n'
        "elif score >= 70:\n"
        '    print("Letter grade: C")\n'
        "else:\n"
        '    print("Letter grade: F")'
    ),
    "lesson_349": (
        "number = 8\n"
        "if number % 2 == 0:\n"
        '    print("Even number!")\n'
        "else:\n"
        '    print("Odd number!")'
    ),
    "lesson_350": (
        "price1 = 60\n"
        "price2 = 55\n"
        "total = price1 + price2\n"
        "if total > 100:\n"
        '    print("You get free shipping!")\n'
        "else:\n"
        '    print("Add more to get free shipping.")'
    ),
    "lesson_351": (
        'first_text = "10"\n'
        'second_text = "10"\n'
        "first_num = int(first_text)\n"
        "second_num = int(second_text)\n"
        "if first_num > second_num:\n"
        '    print("The first number is bigger!")\n'
        "elif second_num > first_num:\n"
        '    print("The second number is bigger!")\n'
        "else:\n"
        '    print("They are equal!")'
    ),
    "lesson_352": (
        "temperature = 65\n"
        "if temperature >= 60:\n"
        '    message = "Wear a t-shirt!"\n'
        "else:\n"
        '    message = "Wear a jacket!"\n'
        "print(message)"
    ),
    "lesson_353": (
        'day = "Saturday"\n'
        'is_holiday = "no"\n'
        'if day == "Saturday" or day == "Sunday" or is_holiday == "yes":\n'
        '    print("No school today!")\n'
        "else:\n"
        '    print("Time for school!")'
    ),
    "lesson_354": (
        'word = "zebra"\n'
        'if "z" in word:\n'
        '    print("Found the letter!")\n'
        "else:\n"
        '    print("Letter not found.")'
    ),
    "lesson_355": (
        'temp_text = "20"\n'
        "temperature = int(temp_text)\n"
        "if temperature >= 90:\n"
        '    print("It\'s a scorcher! Stay hydrated.")\n'
        "elif temperature >= 70:\n"
        '    print("Nice and warm today.")\n'
        "elif temperature >= 50:\n"
        '    print("A bit cool - bring a jacket.")\n'
        "elif temperature >= 32:\n"
        '    print("Chilly! Wear a coat.")\n'
        "else:\n"
        '    print("Freezing! Bundle up warmly.")'
    ),
    "lesson_356": (
        'answer = "YES"\n'
        'if answer.lower() == "yes":\n'
        '    print("Great, let\'s continue!")\n'
        "else:\n"
        '    print("Okay, maybe next time.")'
    ),
    "lesson_357": (
        "temperature = 85\n"
        'is_raining = "no"\n'
        'if is_raining == "yes":\n'
        "    if temperature < 60:\n"
        '        print("Cold and rainy - wear a coat!")\n'
        "    else:\n"
        '        print("Warm rain - grab an umbrella!")\n'
        "else:\n"
        "    if temperature >= 80:\n"
        '        print("Hot and sunny - wear sunscreen!")\n'
        "    else:\n"
        '        print("Nice weather - enjoy the day!")'
    ),
    "lesson_358": (
        'price_text = "10"\n'
        'quantity_text = "6"\n'
        "price = int(price_text)\n"
        "quantity = int(quantity_text)\n"
        "total = price * quantity\n"
        "if total >= 50:\n"
        '    print("Big order! Total: " + str(total))\n'
        "elif total >= 20:\n"
        '    print("Nice order! Total: " + str(total))\n'
        "else:\n"
        '    print("Small order. Total: " + str(total))'
    ),
    # -- conditionals (category_level 21-40) --------------------------------
    "lesson_660": (
        'secret = "1234"\n'
        'guess = "1234"\n'
        "if guess != secret:\n"
        '    print("Access denied.")\n'
        "else:\n"
        '    print("Access granted!")'
    ),
    "lesson_661": (
        "age = 10\n"
        'has_pass = "no"\n'
        'is_vip = "yes"\n'
        'if (age >= 13 and has_pass == "yes") or is_vip == "yes":\n'
        '    print("Welcome to the concert!")\n'
        "else:\n"
        '    print("Sorry, you can\'t come in.")'
    ),
    "lesson_662": (
        "age = 12\n"
        "if 10 <= age <= 15:\n"
        '    print("You are in middle school range!")\n'
        "else:\n"
        '    print("Outside that range.")'
    ),
    "lesson_663": (
        "is_member = True\n"
        "if is_member:\n"
        '    print("Welcome back, member!")\n'
        "else:\n"
        '    print("Please sign up to continue.")'
    ),
    "lesson_664": (
        'day = "Saturday"\n'
        'if day in ["Saturday", "Sunday"]:\n'
        "    print(\"It's the weekend!\")\n"
        "else:\n"
        "    print(\"It's a weekday.\")"
    ),
    "lesson_665": (
        'has_ticket = "yes"\n'
        "age = 8\n"
        'if has_ticket == "yes":\n'
        "    if age >= 13:\n"
        '        print("Enjoy the PG-13 movie!")\n'
        "    elif age >= 6:\n"
        '        print("Enjoy the family movie!")\n'
        "    else:\n"
        '        print("This movie needs an adult with you.")\n'
        "else:\n"
        '    print("You need a ticket first!")'
    ),
    "lesson_666": (
        'age_text = "12"\n'
        "if age_text.isdigit():\n"
        "    age = int(age_text)\n"
        '    print("You are " + str(age) + " years old.")\n'
        "else:\n"
        '    print("That doesn\'t look like a number.")'
    ),
    "lesson_667": (
        "temperature = 85\n"
        'is_windy = "no"\n'
        'if temperature >= 80 and is_windy == "no":\n'
        '    print("Perfect beach day!")\n'
        'elif temperature >= 80 and is_windy == "yes":\n'
        '    print("Hot but windy - hold onto your hat!")\n'
        'elif temperature < 80 and is_windy == "yes":\n'
        '    print("Chilly and windy - wear a jacket!")\n'
        "else:\n"
        '    print("Mild weather today.")'
    ),
    "lesson_668": (
        "score = 60\n"
        'message = "Pass" if score >= 50 else "Fail"\n'
        "print(message)"
    ),
    "lesson_669": (
        "temperature = 70\n"
        'print("Warm" if temperature >= 60 else "Cold")'
    ),
    "lesson_670": (
        'word = "zebra"\n'
        'if "z" not in word:\n'
        '    print("No z here!")\n'
        "else:\n"
        '    print("Found a z!")'
    ),
    "lesson_671": (
        'is_member = "yes"\n'
        "points = 220\n"
        'if is_member == "yes":\n'
        "    if points >= 200:\n"
        '        print("Gold tier!")\n'
        "    elif points >= 100:\n"
        '        print("Silver tier!")\n'
        "    else:\n"
        '        print("Bronze tier!")\n'
        "else:\n"
        '    print("Join to start earning points!")'
    ),
    "lesson_672": (
        "grade = 7\n"
        'has_permission_slip = "yes"\n'
        'if (grade == 6 or grade == 7 or grade == 8) and has_permission_slip == "yes":\n'
        '    print("You can join the field trip!")\n'
        "else:\n"
        '    print("Sorry, you can\'t join this trip.")'
    ),
    "lesson_673": (
        'pet = "dog"\n'
        'if pet == "dog":\n'
        '    print("Woof!")\n'
        'elif pet == "cat":\n'
        '    print("Meow!")\n'
        'elif pet == "hamster":\n'
        '    print("Squeak!")\n'
        "else:\n"
        '    print("Interesting pet!")'
    ),
    "lesson_674": (
        "age = 15\n"
        "if 0 <= age <= 12:\n"
        '    print("Kid")\n'
        "elif 13 <= age <= 19:\n"
        '    print("Teenager")\n'
        "else:\n"
        '    print("Adult")'
    ),
    "lesson_675": (
        'fruit = "kiwi"\n'
        'if fruit in ["apple", "banana", "cherry"]:\n'
        '    print("Common fruit!")\n'
        'elif fruit in ["kiwi", "mango", "dragonfruit"]:\n'
        '    print("Exotic fruit!")\n'
        "else:\n"
        '    print("Never heard of that fruit!")'
    ),
    "lesson_676": (
        "has_key = True\n"
        "has_map = True\n"
        "if has_key and has_map:\n"
        '    print("You can enter the treasure room!")\n'
        "else:\n"
        "    print(\"You're missing something to get in.\")"
    ),
    "lesson_677": (
        "age = 15\n"
        "print(f\"You are a {'kid' if age < 13 else 'teen'}\")"
    ),
    "lesson_678": (
        'role = "admin"\n'
        'day = "Saturday"\n'
        'if role == "admin":\n'
        '    if day in ["Saturday", "Sunday"]:\n'
        '        print("Admin weekend access.")\n'
        "    else:\n"
        '        print("Admin weekday access.")\n'
        "else:\n"
        '    print("Access denied.")'
    ),
    "lesson_679": (
        'ticket_text = "15"\n'
        'has_id = "yes"\n'
        'if ticket_text.isdigit() and has_id == "yes":\n'
        "    age = int(ticket_text)\n"
        "    if age >= 18:\n"
        '        print("Adult ticket: Full price.")\n'
        "    elif age >= 13:\n"
        '        print("Teen ticket: Half price.")\n'
        "    else:\n"
        '        print("Child ticket: Free!")\n'
        "else:\n"
        '    print("You need a valid ticket number and ID.")'
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


def test_conditionals_category_has_a_full_1_to_40_level_progression(engine):
    lessons = engine.lessons_in_category("conditionals")
    assert len(lessons) == 40
    levels = sorted(lesson.category_level for lesson in lessons)
    assert levels == list(range(1, 41))
