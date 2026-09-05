"""Content + behavior checks for every standalone course's (see
app.engine.courses.ALL_COURSES) code lessons (the "What is X?" and "Sample
Program" items in each topic of each chapter -- the quiz items have no code
and are covered by test_course_quiz_content.py instead).

Same invariant as test_fundamentals_lessons.py: unedited starter code must
NOT already satisfy the challenge, and the intended solution must produce
exactly the expected output.
"""
import pytest

from app.engine.courses import ALL_COURSES
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
    "course_advanced_concepts_algorithms_1": (
        'numbers = [4, 2, 7, 1, 9]\n'
        'target = 1\n'
        'for i in range(len(numbers)):\n'
        '    if numbers[i] == target:\n'
        '        print("Found at index " + str(i))\n'
        '        break'
    ),
    "course_advanced_concepts_algorithms_2": (
        'numbers = [9, 3, 7, 1, 5]\n'
        'for i in range(len(numbers)):\n'
        '    for j in range(len(numbers) - 1):\n'
        '        if numbers[j] > numbers[j + 1]:\n'
        '            numbers[j], numbers[j + 1] = numbers[j + 1], numbers[j]\n'
        'print(numbers)'
    ),
    "course_advanced_concepts_recursion_1": (
        'def factorial(n):\n'
        '    if n <= 1:\n'
        '        return 1\n'
        '    return n * factorial(n - 1)\n\n'
        'print(factorial(6))'
    ),
    "course_advanced_concepts_recursion_2": (
        'def sum_list(numbers):\n'
        '    if len(numbers) == 0:\n'
        '        return 0\n'
        '    return numbers[0] + sum_list(numbers[1:])\n\n'
        'print(sum_list([1, 2, 3, 4, 5, 6]))'
    ),
    "course_advanced_concepts_functionalprogramming_1": (
        'numbers = [1, 2, 3, 4]\n'
        'doubled = list(map(lambda x: x * 3, numbers))\n'
        'print(doubled)'
    ),
    "course_advanced_concepts_functionalprogramming_2": (
        'from functools import reduce\n'
        'numbers = [1, 2, 3, 4, 5, 6, 7, 8]\n'
        'evens = list(filter(lambda x: x % 2 == 0, numbers))\n'
        'total = reduce(lambda a, b: a + b, evens)\n'
        'print(evens)\n'
        'print(total)'
    ),
    "course_stdlib_collections_1": (
        'from collections import Counter\n'
        'votes = ["red", "blue", "red", "green", "blue", "red"]\n'
        'counts = Counter(votes)\n'
        'print(counts["blue"])'
    ),
    "course_stdlib_collections_2": (
        'from collections import Counter\n'
        'votes = ["red", "blue", "red", "green", "blue", "red"]\n'
        'counts = Counter(votes)\n'
        'print(counts.most_common(2))'
    ),
    "course_stdlib_itertools_1": (
        'import itertools\n'
        'colors = ["red", "blue"]\n'
        'sizes = ["S", "M", "L"]\n'
        'for combo in itertools.product(colors, sizes):\n'
        '    print(combo)'
    ),
    "course_stdlib_itertools_2": (
        'import itertools\n'
        'morning = ["wake up", "breakfast"]\n'
        'afternoon = ["lunch", "study"]\n'
        'evening = ["dinner"]\n'
        'for task in itertools.chain(morning, afternoon, evening):\n'
        '    print(task)'
    ),
    "course_stdlib_datetime_1": 'import datetime\nbirthday = datetime.date(2016, 9, 3)\nprint(birthday)',
    "course_stdlib_datetime_2": (
        'import datetime\n'
        'start = datetime.date(2024, 1, 1)\n'
        'end = datetime.date(2024, 1, 31)\n'
        'difference = end - start\n'
        'print(difference.days)'
    ),
    "course_stdlib_json_1": 'import json\nprofile = {"name": "Sam", "age": 11}\nprint(json.dumps(profile))',
    "course_stdlib_json_2": (
        'import json\n'
        'data = \'{"name": "Sam", "score": 100}\'\n'
        'profile = json.loads(data)\n'
        'print(profile["score"])'
    ),
    "course_concurrency_concurrencyasync_1": (
        'task_a = ["A1", "A2", "A3"]\n'
        'task_b = ["C1", "C2", "C3"]\n'
        'for a, b in zip(task_a, task_b):\n'
        '    print(a)\n'
        '    print(b)'
    ),
    "course_concurrency_concurrencyasync_2": (
        'tasks = {"download": 3, "process": 3}\n'
        'for round_num in range(1, 4):\n'
        '    for name, steps in tasks.items():\n'
        '        if round_num <= steps:\n'
        '            print(name + " step " + str(round_num))'
    ),
    "course_concurrency_threadscheduling_1": (
        'threads = {"thread-1": 3, "thread-2": 3, "thread-3": 3}\n'
        'for turn in range(1, 4):\n'
        '    for name in threads:\n'
        '        print(name + " runs turn " + str(turn))'
    ),
    "course_concurrency_threadscheduling_2": 'counter = 0\nfor turn in range(7):\n    counter = counter + 1\nprint(counter)',
    "course_concurrency_syncvsasync_1": (
        'def make_tea():\n'
        '    print("Boiling water...")\n'
        '    print("Tea is ready!")\n\n'
        'def make_toast():\n'
        '    print("Toasting bread...")\n'
        '    print("Toast is ready!")\n\n'
        'make_toast()\n'
        'make_tea()'
    ),
    "course_concurrency_syncvsasync_2": (
        'tea_steps = ["Heating water...", "Tea is ready!"]\n'
        'toast_steps = ["Toasting bread...", "Toast is ready!"]\n'
        'for tea, toast in zip(tea_steps, toast_steps):\n'
        '    print(tea)\n'
        '    print(toast)'
    ),
    "course_concurrency_observability_1": (
        'def process_order(order_id):\n'
        '    print("Starting order " + str(order_id))\n'
        '    total = order_id * 10\n'
        '    print("Order " + str(order_id) + " total: " + str(total))\n'
        '    return total\n\n'
        'process_order(5)'
    ),
    "course_concurrency_observability_2": (
        'def divide(a, b):\n'
        '    print("[INFO] Dividing " + str(a) + " by " + str(b))\n'
        '    if b == 0:\n'
        '        print("[ERROR] Cannot divide by zero!")\n'
        '        return None\n'
        '    result = a / b\n'
        '    print("[INFO] Result: " + str(result))\n'
        '    return result\n\n'
        'divide(10, 0)'
    ),
    "ai_foundations_whatisai_1": (
        'temperature = 90\n'
        'if temperature > 85:\n'
        '    print("It\'s hot! Let\'s go swimming.")\n'
        'elif temperature > 60:\n'
        '    print("Nice weather! Let\'s play outside.")\n'
        'else:\n'
        '    print("It\'s chilly. Let\'s stay in and read.")'
    ),
    "ai_foundations_whatisai_2": (
        'temperature = 75\n'
        'is_raining = True\n'
        'if temperature > 85 and not is_raining:\n'
        '    print("It\'s hot and dry! Let\'s go swimming.")\n'
        'elif is_raining:\n'
        '    print("It\'s raining. Let\'s stay in and read.")\n'
        'else:\n'
        '    print("Nice weather! Let\'s play outside.")'
    ),
    "ai_foundations_rulebased_1": (
        'symptom = "fever"\n'
        'if symptom == "cough":\n'
        '    print("Advice: Drink warm water and rest.")\n'
        'elif symptom == "fever":\n'
        '    print("Advice: Rest and monitor your temperature.")\n'
        'elif symptom == "headache":\n'
        '    print("Advice: Drink water and rest in a quiet room.")\n'
        'else:\n'
        '    print("Advice: Talk to a grown-up about how you feel.")'
    ),
    "ai_foundations_rulebased_2": (
        'message = "what\'s your name?"\n'
        'message = message.lower()\n'
        'if "hello" in message:\n'
        '    print("Hi there! I\'m a simple rule-based chatbot.")\n'
        'elif "weather" in message:\n'
        '    print("I can\'t check the weather, but I hope it\'s nice!")\n'
        'elif "name" in message:\n'
        '    print("I\'m RoboBot, a rule-based chatbot!")\n'
        'else:\n'
        '    print("I don\'t understand yet, but I\'m still learning!")'
    ),
    "ai_tools_whatisml_1": (
        'training_examples = {"cat": "meow", "dog": "woof", "cow": "moo", "duck": "quack"}\n'
        'print("The robot learned these examples:")\n'
        'for animal, sound in training_examples.items():\n'
        '    print(animal + " -> " + sound)'
    ),
    "ai_tools_whatisml_2": (
        'training_data = {"cat": "meow", "dog": "woof", "cow": "moo", "duck": "quack"}\n'
        'test_word = "duck"\n'
        'guess = training_data.get(test_word, "Not sure yet!")\n'
        'print("The robot guesses: " + guess)'
    ),
    "ai_tools_whatismcp_1": (
        'def get_weather(city):\n'
        '    return "Sunny in " + city\n\n'
        'request = {"tool": "get_weather", "city": "Tokyo"}\n'
        'print("The AI is asking for tool: " + request["tool"])\n'
        'result = get_weather(request["city"])\n'
        'print("The tool replied: " + result)'
    ),
    "ai_tools_whatismcp_2": (
        'def get_weather(city):\n'
        '    return "Sunny in " + city\n\n'
        'def get_time(city):\n'
        '    return "It\'s 3:00 PM in " + city\n\n'
        'tools = {"get_weather": get_weather, "get_time": get_time}\n'
        'request = {"tool": "get_time", "args": {"city": "Paris"}}\n\n'
        'tool_function = tools[request["tool"]]\n'
        'result = tool_function(request["args"]["city"])\n'
        'print(result)'
    ),
}


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_every_course_code_lesson_has_a_solution_fixture(engine):
    code_lesson_ids = {
        lesson.id
        for course in ALL_COURSES
        for category in course.categories
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
