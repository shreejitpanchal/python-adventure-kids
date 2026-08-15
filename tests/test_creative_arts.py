"""Content checks for the Creative Arts turtle-graphics track: each lesson's
example_code must run cleanly against a real GameCanvas and satisfy its own
ast_contains -- and for closed shapes, the turtle should end up back where
it started, confirming the turn-angle math is actually correct."""
import tkinter as tk

import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_ast_contains
from app.games.game_canvas import GameCanvas
from app.games.graphical_runner import run_graphical_code

ART_IDS = [f"art_{i:02d}" for i in range(1, 9)]

# Lessons that trace a closed shape back to the turtle's starting point
# (50, 50) -- see _TURTLE_START_X/Y in app/games/game_canvas.py.
CLOSED_SHAPE_IDS = ["art_04", "art_05", "art_06", "art_07", "art_08"]


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


@pytest.fixture
def game_canvas():
    root = tk.Tk()
    root.withdraw()
    canvas = tk.Canvas(root)
    gc = GameCanvas(canvas, root)
    yield gc
    root.destroy()


def test_all_eight_creative_arts_lessons_are_registered(engine):
    arts = engine.lessons_in_category("creative_arts")
    assert {lesson.id for lesson in arts} == set(ART_IDS)
    assert sorted(lesson.category_level for lesson in arts) == list(range(1, 9))


@pytest.mark.parametrize("lesson_id", ART_IDS)
def test_is_a_bonus_graphical_level_with_ast_contains_set(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert lesson.main_path is False
    assert lesson.graphical is True
    assert lesson.ast_contains, f"{lesson_id} should declare ast_contains"


@pytest.mark.parametrize("lesson_id", ART_IDS)
def test_example_code_runs_cleanly_and_satisfies_ast_contains(engine, lesson_id, game_canvas):
    lesson = engine.get(lesson_id)
    result = run_graphical_code(lesson.example_code.strip(), game_canvas)
    assert result.success is True, f"{lesson_id} failed: {result.traceback_text}"
    assert validate_ast_contains(lesson.example_code, lesson.ast_contains) is True


@pytest.mark.parametrize("lesson_id", CLOSED_SHAPE_IDS)
def test_closed_shape_returns_to_the_starting_point(engine, lesson_id, game_canvas):
    lesson = engine.get(lesson_id)
    run_graphical_code(lesson.example_code.strip(), game_canvas)
    assert (game_canvas._turtle_x, game_canvas._turtle_y) == pytest.approx((50.0, 50.0), abs=0.01), (
        f"{lesson_id}'s turn angle doesn't close the shape back to the start"
    )
