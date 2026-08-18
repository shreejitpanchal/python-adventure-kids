"""Content + behavior checks for the "🎓 Python Learning" course's 12 code
lessons (the "What is X?" and "Sample Program" items in each of the 6
chapters -- the 6 quiz items have no code and are covered by
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
    "course_control_flow_1": (
        'for i in range(4):\n'
        '    if i == 1:\n'
        '        print("one!")\n'
        '    else:\n'
        '        print("not one")'
    ),
    "course_control_flow_2": (
        'for number in range(1, 11):\n'
        '    if number % 2 == 0:\n'
        '        print(str(number) + " is even")\n'
        '    else:\n'
        '        print(str(number) + " is odd")'
    ),
    "course_functions_1": (
        'def greet(name):\n'
        '    return "Hello, " + name + "!"\n\n'
        'message = greet("Robin")\n'
        'print(message)'
    ),
    "course_functions_2": (
        'def introduce(name, age):\n'
        '    return name + " is " + str(age) + " years old"\n\n'
        'print(introduce("Jamie", 10))\n'
        'print(introduce("Casey", 12))'
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
