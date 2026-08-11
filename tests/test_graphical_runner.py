import time
import tkinter as tk

import pytest

from app.games.game_canvas import GameCanvas
from app.games.graphical_runner import run_graphical_code


@pytest.fixture
def game_canvas():
    root = tk.Tk()
    root.withdraw()
    canvas = tk.Canvas(root)
    gc = GameCanvas(canvas, root)
    yield gc, canvas, root
    root.destroy()


def test_simple_code_runs_successfully(game_canvas):
    gc, canvas, root = game_canvas
    result = run_graphical_code('game.set_background("black")', gc)
    assert result.success is True
    assert canvas.cget("bg") == "black"


def test_drawing_and_moving_via_the_game_object(game_canvas):
    gc, canvas, root = game_canvas
    code = (
        'snake = game.draw_rect(50, 50, 20, 20, "green")\n'
        'game.move_shape(snake, 10, 0)\n'
    )
    result = run_graphical_code(code, gc)
    assert result.success is True
    assert len(canvas.find_all()) == 1


def test_blocked_import_never_executes(game_canvas):
    gc, canvas, root = game_canvas
    result = run_graphical_code("import os\ngame.set_background('black')", gc)
    assert result.blocked is True
    assert canvas.cget("bg") != "black"


def test_while_loop_is_blocked_in_graphical_mode(game_canvas):
    gc, canvas, root = game_canvas
    result = run_graphical_code("while True:\n    pass", gc)
    assert result.blocked is True
    assert "freeze" in result.blocked_message


def test_runtime_error_is_captured_not_raised(game_canvas):
    gc, canvas, root = game_canvas
    result = run_graphical_code("game.draw_rect(1, 2, 3, 4)\nprint(1 / 0)", gc)
    assert result.success is False
    assert result.blocked is False
    assert "ZeroDivisionError" in result.traceback_text


def test_self_scheduling_after_call_returns_immediately(game_canvas):
    gc, canvas, root = game_canvas
    code = (
        'snake = game.draw_rect(0, 0, 10, 10, "green")\n'
        "def move_snake():\n"
        "    game.move_shape(snake, 10, 0)\n"
        "    game.after(300, move_snake)\n"
        "move_snake()\n"
    )
    start = time.time()
    result = run_graphical_code(code, gc)
    elapsed = time.time() - start

    assert result.success is True
    assert elapsed < 1.0, "top-level exec should return immediately; the game loop runs via Tk's own after()"


def test_random_module_is_usable_in_graphical_lessons(game_canvas):
    gc, canvas, root = game_canvas
    result = run_graphical_code(
        "import random\nx = random.randint(0, 100)\ngame.draw_rect(x, 0, 5, 5)", gc,
    )
    assert result.success is True
