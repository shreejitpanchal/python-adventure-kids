"""Content + behavior checks for the first Snake project steps (16-18): each
step's starter code must actually run cleanly against a real GameCanvas."""
import tkinter as tk

import pytest

from app.engine.lesson_engine import LessonEngine
from app.games.game_canvas import GameCanvas
from app.games.graphical_runner import run_graphical_code

SNAKE_LESSON_IDS = ["lesson_16", "lesson_17", "lesson_18"]


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


def test_snake_lessons_are_not_part_of_todays_mission(engine):
    # Snake is reachable only through the category browser now -- see
    # test_categories.py's TODAYS_MISSION_CATEGORIES coverage for why.
    mission_ids = {lesson.id for lesson in engine.main_path_lessons()}
    for lesson_id in SNAKE_LESSON_IDS:
        assert lesson_id not in mission_ids
    assert engine.next_after("lesson_18") is None


@pytest.mark.parametrize("lesson_id", SNAKE_LESSON_IDS)
def test_lesson_is_marked_graphical(engine, lesson_id):
    assert engine.get(lesson_id).graphical is True


@pytest.mark.parametrize("lesson_id", SNAKE_LESSON_IDS)
def test_starter_code_runs_cleanly_against_a_real_canvas(engine, lesson_id, game_canvas):
    lesson = engine.get(lesson_id)
    result = run_graphical_code(lesson.starter_code.strip(), game_canvas)
    assert result.success is True, result.traceback_text


def test_step_16_sets_title_and_background(engine, game_canvas):
    lesson = engine.get("lesson_16")
    run_graphical_code(lesson.starter_code.strip(), game_canvas)
    assert game_canvas._canvas.cget("bg") == "black"
    assert game_canvas._window.title() == "My Snake Game"


def test_step_17_draws_a_snake_rectangle(engine, game_canvas):
    lesson = engine.get("lesson_17")
    run_graphical_code(lesson.starter_code.strip(), game_canvas)
    assert len(game_canvas._canvas.find_all()) == 1


def test_step_18_schedules_movement_without_blocking(engine, game_canvas):
    import time

    lesson = engine.get("lesson_18")
    start = time.time()
    result = run_graphical_code(lesson.starter_code.strip(), game_canvas)
    elapsed = time.time() - start

    assert result.success is True
    assert elapsed < 1.0
    assert len(game_canvas._canvas.find_all()) == 1
