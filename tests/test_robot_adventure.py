"""Content checks for the Flet-only Robot Adventure track: each lesson's
example_code must run cleanly against a real Flet GameCanvas, satisfy its
own ast_contains, and -- for every lesson (all six of these declare
requires_goal_reached) -- actually leave the robot at the goal, so a
broken mission can't silently ship. Same execution path
lesson_screen_flet.py uses for graphical lessons; no CTk equivalent
exists (see game_canvas.py's module docstring for the Flet-only
rationale, matching Arcade Lab)."""
import flet as ft
import flet.canvas as cv
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_ast_contains
from app.games.game_canvas_flet import GameCanvas
from app.sandbox.inprocess_runner import run_code

ROBOT_IDS = [f"lesson_{n}" for n in range(440, 446)]


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


class FakePage:
    def update(self) -> None:
        pass


def make_game_canvas() -> GameCanvas:
    canvas = cv.Canvas(shapes=[])
    container = ft.Container(content=canvas)
    title_text = ft.Text("")
    return GameCanvas(canvas, container, title_text, FakePage())


def test_all_six_robot_adventure_lessons_are_registered(engine):
    lessons = engine.lessons_in_category("robot_adventure")
    assert {lesson.id for lesson in lessons} == set(ROBOT_IDS)
    assert sorted(lesson.category_level for lesson in lessons) == list(range(1, 7))


@pytest.mark.parametrize("lesson_id", ROBOT_IDS)
def test_is_a_bonus_graphical_level_requiring_the_goal(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert lesson.main_path is False
    assert lesson.graphical is True
    assert lesson.category == "robot_adventure"
    assert lesson.requires_goal_reached is True
    assert lesson.ast_contains, f"{lesson_id} should declare ast_contains"


@pytest.mark.parametrize("lesson_id", ROBOT_IDS)
def test_example_code_satisfies_its_own_ast_contains(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert validate_ast_contains(lesson.example_code, lesson.ast_contains) is True


@pytest.mark.parametrize("lesson_id", ROBOT_IDS)
def test_example_code_runs_cleanly_and_reaches_the_goal(engine, lesson_id):
    lesson = engine.get(lesson_id)
    game = make_game_canvas()
    result = run_code(lesson.example_code.strip(), game=game, disallow_while=True)
    assert result.success is True, f"{lesson_id} failed: {result.stderr}"
    assert game.robot_at_goal() is True, f"{lesson_id}'s example code doesn't reach the goal"


def test_coin_collector_lesson_actually_collects_both_coins(engine):
    lesson = engine.get("lesson_443")
    game = make_game_canvas()
    run_code(lesson.example_code.strip(), game=game, disallow_while=True)
    assert game.coins_collected() == 2


def test_sense_the_wall_lesson_turns_only_once(engine):
    """The capstone lesson should navigate the corner via robot_wall_ahead(),
    not by luck -- confirm it actually changed direction along the way."""
    lesson = engine.get("lesson_445")
    game = make_game_canvas()
    run_code(lesson.example_code.strip(), game=game, disallow_while=True)
    assert game._robot_facing == "S"  # started facing E, turned right once at the edge


def test_lessons_are_not_accidentally_solvable_without_editing_broken_starter():
    """Unlike Code Crackers, these are correct-by-design (starter_code ==
    example_code, matching Creative Arts/Arcade Lab's convention) -- this
    just confirms starter_code wasn't left out of sync with example_code."""
    engine = LessonEngine()
    for lesson_id in ROBOT_IDS:
        lesson = engine.get(lesson_id)
        assert lesson.starter_code == lesson.example_code
