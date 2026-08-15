"""Content checks for the RPG Quests track: each lesson's starter_code must
run cleanly but produce the wrong output (missing the taught construct),
while example_code is the working, complete version -- same
edit-required invariant as the bonus arithmetic levels
(tests/test_bonus_levels.py), plus an ast_contains check where the lesson
declares one."""
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_ast_contains, validate_output
from app.sandbox.runner import run_code

RPG_IDS = [f"rpg_{i:02d}" for i in range(1, 9)]


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


def test_all_eight_rpg_quests_are_registered(engine):
    rpgs = engine.lessons_in_category("rpg_quests")
    assert {lesson.id for lesson in rpgs} == set(RPG_IDS)
    assert sorted(lesson.category_level for lesson in rpgs) == list(range(1, 9))


@pytest.mark.parametrize("lesson_id", RPG_IDS)
def test_is_a_bonus_level(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert lesson.main_path is False
    assert lesson.next_lesson_id is None


@pytest.mark.parametrize("lesson_id", RPG_IDS)
def test_starter_code_runs_but_does_not_satisfy_the_challenge(engine, lesson_id):
    lesson = engine.get(lesson_id)
    result = run_code(lesson.starter_code.strip())
    assert result.success is True, f"{lesson_id} starter code failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is False, (
        f"{lesson_id}'s starter code already satisfies the challenge without editing"
    )


@pytest.mark.parametrize("lesson_id", RPG_IDS)
def test_example_code_satisfies_the_challenge(engine, lesson_id):
    lesson = engine.get(lesson_id)
    result = run_code(lesson.example_code.strip())
    assert result.success is True, f"{lesson_id} example code failed to run: {result.stderr}"
    assert validate_output(result.stdout, lesson.expected_output) is True, (
        f"{lesson_id} produced {result.stdout!r}, expected {lesson.expected_output!r}"
    )
    if lesson.ast_contains:
        assert validate_ast_contains(lesson.example_code, lesson.ast_contains) is True
