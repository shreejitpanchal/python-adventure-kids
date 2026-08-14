import threading
import time
import tkinter as tk

import pytest

from app.games.game_canvas import GameCanvas
from app.sandbox.inprocess_runner import RunHandle, run_code


def test_successful_run_captures_stdout():
    result = run_code('print("Hello!")')
    assert result.success is True
    assert result.stdout.strip() == "Hello!"
    assert result.blocked is False
    assert result.timed_out is False


def test_syntax_error_is_reported_not_blocked():
    result = run_code('print("Hello!"')
    assert result.success is False
    assert result.blocked is False
    assert "SyntaxError" in result.stderr


def test_runtime_error_is_reported():
    result = run_code("print(1 / 0)")
    assert result.success is False
    assert "ZeroDivisionError" in result.stderr


def test_blocked_import_never_executes():
    result = run_code("import os\nprint('should not run')")
    assert result.blocked is True
    assert result.stdout == ""


def test_blocked_dangerous_call_never_executes():
    result = run_code("eval('1+1')")
    assert result.blocked is True


def test_infinite_loop_times_out():
    result = run_code("while True:\n    pass", timeout=1.5)
    assert result.timed_out is True
    assert result.success is False


def test_cancel_stops_a_running_loop():
    handle = RunHandle()
    handle.cancel()
    # Cancelling before the run even starts should still stop it almost
    # immediately, well before the (generous) timeout elapses.
    result = run_code("while True:\n    pass", timeout=5, handle=handle)
    assert result.timed_out is True


def test_cancel_is_detected_promptly_from_another_thread():
    handle = RunHandle()

    def cancel_soon():
        time.sleep(0.1)
        handle.cancel()

    threading.Thread(target=cancel_soon).start()

    start = time.time()
    result = run_code("while True:\n    pass", timeout=30, handle=handle)
    elapsed = time.time() - start

    assert result.timed_out is True
    assert elapsed < 5, "cancellation should be picked up well before the 30s timeout"


def test_input_reads_from_provided_stdin():
    result = run_code('name = input("Name? ")\nprint("Hi " + name)', stdin_text="Sam\n")
    assert result.success is True
    assert result.stdout == "Name? Hi Sam\n"


def test_input_without_stdin_fails_fast_with_eof_instead_of_hanging():
    start = time.time()
    result = run_code("print(input())", timeout=5)
    elapsed = time.time() - start

    assert result.success is False
    assert result.timed_out is False
    assert "EOFError" in result.stderr
    assert elapsed < 4, "should fail immediately on EOF, not wait out the timeout"


def test_random_module_is_usable_end_to_end():
    result = run_code("import random\nn = random.randint(1, 10)\nprint(1 <= n <= 10)")
    assert result.success is True
    assert result.stdout.strip() == "True"


def test_disallowed_module_is_blocked_even_though_random_is_allowed():
    result = run_code("import subprocess")
    assert result.blocked is True


def test_large_but_fast_loop_completes_without_a_false_timeout():
    result = run_code("total = 0\nfor i in range(200000):\n    total += i\nprint(total)", timeout=5)
    assert result.success is True
    assert result.stdout.strip() == str(sum(range(200000)))


def test_only_one_run_executes_at_a_time_without_corrupting_stdout():
    results = {}

    def run_one(key, text):
        results[key] = run_code(f'print("{text}" * 1000)')

    t1 = threading.Thread(target=run_one, args=("a", "A"))
    t2 = threading.Thread(target=run_one, args=("b", "B"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["a"].stdout.strip() == "A" * 1000
    assert results["b"].stdout.strip() == "B" * 1000


# -- graphical lessons (folded in from the old app/games/graphical_runner.py) -----

@pytest.fixture
def game_canvas():
    root = tk.Tk()
    root.withdraw()
    canvas = tk.Canvas(root)
    gc = GameCanvas(canvas, root)
    yield gc, canvas, root
    root.destroy()


def test_graphical_code_runs_successfully(game_canvas):
    gc, canvas, root = game_canvas
    result = run_code('game.set_background("black")', game=gc, disallow_while=True)
    assert result.success is True
    assert canvas.cget("bg") == "black"


def test_graphical_drawing_and_moving_via_the_game_object(game_canvas):
    gc, canvas, root = game_canvas
    code = 'snake = game.draw_rect(50, 50, 20, 20, "green")\ngame.move_shape(snake, 10, 0)\n'
    result = run_code(code, game=gc, disallow_while=True)
    assert result.success is True
    assert len(canvas.find_all()) == 1


def test_graphical_blocked_import_never_executes(game_canvas):
    gc, canvas, root = game_canvas
    result = run_code("import os\ngame.set_background('black')", game=gc, disallow_while=True)
    assert result.blocked is True
    assert canvas.cget("bg") != "black"


def test_while_loop_is_blocked_in_graphical_mode(game_canvas):
    gc, canvas, root = game_canvas
    result = run_code("while True:\n    pass", game=gc, disallow_while=True)
    assert result.blocked is True
    assert "freeze" in result.blocked_message


def test_graphical_runtime_error_is_captured_not_raised(game_canvas):
    gc, canvas, root = game_canvas
    result = run_code("game.draw_rect(1, 2, 3, 4)\nprint(1 / 0)", game=gc, disallow_while=True)
    assert result.success is False
    assert result.blocked is False
    assert "ZeroDivisionError" in result.stderr


def test_graphical_self_scheduling_after_call_returns_immediately(game_canvas):
    gc, canvas, root = game_canvas
    code = (
        'snake = game.draw_rect(0, 0, 10, 10, "green")\n'
        "def move_snake():\n"
        "    game.move_shape(snake, 10, 0)\n"
        "    game.after(300, move_snake)\n"
        "move_snake()\n"
    )
    start = time.time()
    result = run_code(code, game=gc, disallow_while=True)
    elapsed = time.time() - start

    assert result.success is True
    assert elapsed < 1.0, "top-level exec should return immediately; the game loop runs via Tk's own after()"


def test_graphical_random_module_is_usable(game_canvas):
    gc, canvas, root = game_canvas
    result = run_code(
        "import random\nx = random.randint(0, 100)\ngame.draw_rect(x, 0, 5, 5)", game=gc, disallow_while=True,
    )
    assert result.success is True
