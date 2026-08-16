"""Content checks for the 3 lessons authored specifically for Python
Journey (lesson_450/451/452) -- real sandbox execution, matching every
other content track this session, plus confirms starter_code correctly
does/doesn't already satisfy each lesson's challenge (edit-required vs.
press-run, per lesson)."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_ast_contains, validate_output
from app.sandbox.inprocess_runner import run_code


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_all_three_journey_lessons_are_registered_bonus_levels(engine):
    for lesson_id in ["lesson_450", "lesson_451", "lesson_452"]:
        lesson = engine.get(lesson_id)
        assert lesson.main_path is False
        assert lesson.category == "journey_projects" or lesson.category == "basics"
        assert lesson.concept_tags, f"{lesson_id} should declare concept_tags"


def test_lesson_450_comments_is_press_run_style(engine):
    lesson = engine.get("lesson_450")
    assert lesson.learning_path_module == "python-starter"
    assert lesson.lesson_type == "learn"

    result = run_code(lesson.starter_code.strip())
    assert result.success is True, result.stderr
    assert validate_output(result.stdout, lesson.expected_output) is True


def test_lesson_451_intro_card_requires_editing(engine):
    lesson = engine.get("lesson_451")
    assert lesson.learning_path_module == "python-starter"
    assert lesson.lesson_type == "project"
    assert lesson.category == "journey_projects"
    assert lesson.category_level == 1

    starter_result = run_code(lesson.starter_code.strip())
    assert starter_result.success is True, starter_result.stderr
    assert validate_output(starter_result.stdout, lesson.expected_output) is False, (
        "starter_code should NOT already satisfy the challenge -- it's edit-required"
    )

    solved = (
        'print("=====================")\n'
        'print("MEET AVYAAN THE CODER")\n'
        'print("=====================")\n'
        "# Favorite number, just for fun\n"
        "favorite_number = 42\n"
        'print("Favorite number:", favorite_number)\n'
        'print("Loves: Python, games, and swimming!")'
    )
    result = run_code(solved)
    assert result.success is True, result.stderr
    assert validate_output(result.stdout, lesson.expected_output) is True
    assert validate_ast_contains(solved, lesson.ast_contains) is True


def test_lesson_452_player_profile_requires_editing_and_uses_input(engine):
    lesson = engine.get("lesson_452")
    assert lesson.learning_path_module == "variables-and-input"
    assert lesson.lesson_type == "project"
    assert lesson.category == "journey_projects"
    assert lesson.category_level == 2
    assert lesson.input_prompt

    starter_result = run_code(lesson.starter_code.strip(), stdin_text="11\n")
    assert starter_result.success is True, starter_result.stderr
    assert validate_output(starter_result.stdout, lesson.expected_output, input_value="11") is False, (
        "starter_code should NOT already satisfy the challenge -- it's edit-required"
    )

    solved = (
        'age = int(input("How old are you? "))\n'
        'name = "Ava"\n'
        'favorite_color = "purple"\n'
        'print(f"{name} is {age} years old and loves {favorite_color}!")'
    )
    result = run_code(solved, stdin_text="11\n")
    assert result.success is True, result.stderr
    assert validate_output(result.stdout, lesson.expected_output, input_value="11") is True
    assert validate_ast_contains(solved, lesson.ast_contains) is True


def test_journey_projects_category_has_exactly_the_two_new_lessons(engine):
    lessons = engine.lessons_in_category("journey_projects")
    assert {lesson.id for lesson in lessons} == {"lesson_451", "lesson_452"}
    assert sorted(lesson.category_level for lesson in lessons) == [1, 2]
