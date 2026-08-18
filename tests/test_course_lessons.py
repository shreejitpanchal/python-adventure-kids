"""Content + behavior checks for the "🎓 Python Learning" course's code
lessons (the "What is X?" and "Sample Program" items in each topic of
each chapter -- the quiz items have no code and are covered by
test_course_quiz_content.py instead).

Same invariant as test_fundamentals_lessons.py: unedited starter code must
NOT already satisfy the challenge, and the intended solution must produce
exactly the expected output.
"""
import pytest

from app.engine.categories import COURSE_CATEGORIES
from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_output
from app.sandbox.runner import run_code

LESSON_SOLUTIONS = {
    "course_intro_setup_1": 'print("Hello, world!")',
    "course_intro_setup_2": (
        '# My About Me program\n'
        'print("My name is Alex")\n'
        'print("I am learning Python!")\n'
        'print("Python is fun!")'
    ),
    "course_intro_setup_comments_1": 'print("Hello!")\nprint("This won\'t show")\nprint("Goodbye!")',
    "course_intro_setup_comments_2": (
        '# Step 1: greet the user\n'
        'print("Hello!")\n'
        '# Step 2: ask how they are\n'
        'print("How are you?")\n'
        '# Step 3: say goodbye\n'
        'print("Goodbye!")'
    ),
    "course_intro_setup_errors_1": 'print("Goodbye!")',
    "course_intro_setup_errors_2": 'score = 250\nprint("Score: " + str(score))',
    "course_variables_1": 'name = "Robin"\nage = 11\nprint(name)\nprint(age)',
    "course_variables_2": (
        'name = "Jamie"\n'
        'age = 12\n'
        'height = 5.0\n'
        'is_student = False\n'
        'print(name)\n'
        'print(age)\n'
        'print(height)\n'
        'print(is_student)\n'
        'print("Age as text: " + str(age))'
    ),
    "course_control_flow_1": 'age = 5\nif age >= 8:\n    print("You can play!")\nelse:\n    print("You are too young!")',
    "course_control_flow_2": (
        'score = 95\n'
        'if score >= 90:\n'
        '    print("Grade: A")\n'
        'elif score >= 80:\n'
        '    print("Grade: B")\n'
        'else:\n'
        '    print("Grade: C")'
    ),
    "course_control_flow_forloops_1": 'for i in range(5):\n    print("Hooray!")',
    "course_control_flow_forloops_2": 'for number in range(1, 11):\n    print(number * 2)',
    "course_control_flow_whileloops_1": (
        'count = 0\n'
        'while count < 5:\n'
        '    print("Counting: " + str(count))\n'
        '    count = count + 1'
    ),
    "course_control_flow_whileloops_2": (
        'countdown = 3\n'
        'while countdown > 0:\n'
        '    print(countdown)\n'
        '    countdown = countdown - 1\n'
        'print("Liftoff!")'
    ),
    "course_functions_1": 'def greet():\n    print("Howdy!")\n\ngreet()',
    "course_functions_2": 'def greet():\n    print("Hello!")\n\ngreet()\ngreet()\ngreet()',
    "course_functions_parameters_1": 'def greet(name):\n    print("Hello, " + name + "!")\n\ngreet("Robin")',
    "course_functions_parameters_2": (
        'def introduce(name, age):\n'
        '    print(name + " is " + str(age) + " years old")\n\n'
        'introduce("Robin", 11)'
    ),
    "course_functions_returnvalues_1": 'def add_five(number):\n    return number + 5\n\nresult = add_five(20)\nprint(result)',
    "course_functions_returnvalues_2": (
        'def square(number):\n'
        '    return number * number\n\n'
        'result = square(6)\n'
        'print("Squared: " + str(result))'
    ),
    "course_lists_1": (
        'fruits = ["apple", "banana", "orange"]\n'
        'print(fruits[2])\n'
        'print(len(fruits))'
    ),
    "course_lists_2": (
        'foods = ["pizza", "tacos", "pasta"]\n'
        'foods.append("sushi")\n'
        'foods.append("ramen")\n'
        'for i in range(len(foods)):\n'
        '    print(str(i) + ": " + foods[i])'
    ),
    "course_capstone_1": (
        'tasks = []\n\n'
        'def show_tasks(tasks):\n'
        '    if len(tasks) == 0:\n'
        '        print("No tasks yet!")\n'
        '    else:\n'
        '        for task in tasks:\n'
        '            print("- " + task)\n\n'
        'show_tasks(tasks)'
    ),
    "course_capstone_2": (
        'tasks = []\n\n'
        'def add_task(task):\n'
        '    tasks.append(task)\n\n'
        'add_task("Buy milk")\n'
        'add_task("Walk the dog")\n'
        'add_task("Do homework")\n\n'
        'if len(tasks) == 0:\n'
        '    print("No tasks yet!")\n'
        'else:\n'
        '    for i in range(len(tasks)):\n'
        '        print(str(i + 1) + ". " + tasks[i])'
    ),
    "course_tuples_1": 'point = (7, 2)\nprint(point[0])\nprint(point[1])',
    "course_tuples_2": (
        'students = [("Sam", 9), ("Robin", 11), ("Jamie", 10)]\n'
        'for name, age in students:\n'
        '    print(name + " is " + str(age) + " years old")'
    ),
    "course_dictionaries_1": 'person = {"name": "Robin", "age": 11}\nprint(person["name"])\nprint(person["age"])',
    "course_dictionaries_2": (
        'person = {"name": "Sam", "age": 9}\n'
        'person["favorite_color"] = "blue"\n'
        'person["city"] = "Austin"\n'
        'for key, value in person.items():\n'
        '    print(key + ": " + str(value))'
    ),
    "course_sets_1": 'colors = {"red", "green", "blue", "red", "yellow"}\nprint(len(colors))\nprint(sorted(colors))',
    "course_sets_2": (
        'fruits = {"apple", "banana"}\n'
        'fruits.add("orange")\n'
        'fruits.add("apple")\n'
        'fruits.add("mango")\n'
        'print(len(fruits))\n'
        'print("banana" in fruits)\n'
        'print(sorted(fruits))'
    ),
    "course_variables_numbers_1": 'age = 12\nheight = 5.5\nprint(age)\nprint(height)\nprint(age + height)',
    "course_variables_numbers_2": (
        'width = 5\n'
        'length = 8\n'
        'area = width * length\n'
        'perimeter = 2 * (width + length)\n'
        'print("Area: " + str(area))\n'
        'print("Perimeter: " + str(perimeter))'
    ),
    "course_variables_strings_1": 'greeting = "Hello"\nname = "Robin"\nprint(greeting + ", " + name + "!")\nprint(len(name))',
    "course_variables_strings_2": 'word = "coding"\nprint(word.upper())\nprint(word[0])\nprint(word[0:3])',
    "course_variables_booleans_1": 'is_sunny = False\nis_raining = True\nprint(is_sunny)\nprint(is_raining)\nprint(5 > 3)',
    "course_variables_booleans_2": 'age = 5\nhas_ticket = True\ncan_enter = age >= 8 and has_ticket\nprint(can_enter)',
    "course_variables_typeconversion_1": 'age = 12\nage_text = str(age)\nprint("I am " + age_text + " years old")',
    "course_variables_typeconversion_2": (
        'quantity_text = "5"\n'
        'quantity = int(quantity_text)\n'
        'price = 2\n'
        'total = quantity * price\n'
        'print(total)'
    ),
}


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_every_course_code_lesson_has_a_solution_fixture(engine):
    code_lesson_ids = {
        lesson.id
        for category in COURSE_CATEGORIES
        for lesson in engine.lessons_in_category(category)
        if not lesson.is_quiz
    }
    assert code_lesson_ids == set(LESSON_SOLUTIONS)


@pytest.mark.parametrize("lesson_id", list(LESSON_SOLUTIONS))
def test_unedited_starter_code_does_not_satisfy_the_challenge(engine, lesson_id):
    lesson = engine.get(lesson_id)
    result = run_code(lesson.starter_code.strip())
    assert result.success is True, f"{lesson_id} starter code failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is False, (
        f"{lesson_id}'s starter code already satisfies the challenge without editing"
    )


@pytest.mark.parametrize("lesson_id,solution", LESSON_SOLUTIONS.items())
def test_intended_solution_satisfies_the_challenge(engine, lesson_id, solution):
    lesson = engine.get(lesson_id)
    result = run_code(solution)
    assert result.success is True, f"{lesson_id} solution failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is True, (
        f"{lesson_id}'s intended solution produced {result.stdout!r}, expected {lesson.expected_output!r}"
    )
