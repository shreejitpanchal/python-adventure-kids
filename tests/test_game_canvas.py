import tkinter as tk

import pytest

from app.games.game_canvas import GameCanvas


@pytest.fixture
def game_canvas():
    root = tk.Tk()
    root.withdraw()
    canvas = tk.Canvas(root)
    gc = GameCanvas(canvas, root)
    yield gc, canvas, root
    root.destroy()


def test_set_title(game_canvas):
    gc, canvas, root = game_canvas
    gc.set_title("My Snake Game")
    assert root.title() == "My Snake Game"


def test_set_background(game_canvas):
    gc, canvas, root = game_canvas
    gc.set_background("black")
    assert canvas.cget("bg") == "black"


def test_draw_rect_creates_a_rectangle_at_the_right_position(game_canvas):
    gc, canvas, root = game_canvas
    shape_id = gc.draw_rect(10, 20, 30, 40, "green")
    coords = canvas.coords(shape_id)
    assert coords == [10.0, 20.0, 40.0, 60.0]
    assert canvas.itemcget(shape_id, "fill") == "green"


def test_move_shape_moves_relative_to_current_position(game_canvas):
    gc, canvas, root = game_canvas
    shape_id = gc.draw_rect(0, 0, 10, 10)
    gc.move_shape(shape_id, 5, 7)
    x, y = gc.get_shape_position(shape_id)
    assert (x, y) == (5.0, 7.0)


def test_set_shape_position_moves_to_an_absolute_position_keeping_size(game_canvas):
    gc, canvas, root = game_canvas
    shape_id = gc.draw_rect(0, 0, 10, 20)
    gc.set_shape_position(shape_id, 100, 200)
    coords = canvas.coords(shape_id)
    assert coords == [100.0, 200.0, 110.0, 220.0]


def test_delete_shape_removes_it(game_canvas):
    gc, canvas, root = game_canvas
    shape_id = gc.draw_rect(0, 0, 10, 10)
    gc.delete_shape(shape_id)
    assert canvas.coords(shape_id) == []


def test_clear_removes_everything(game_canvas):
    gc, canvas, root = game_canvas
    gc.draw_rect(0, 0, 10, 10)
    gc.draw_rect(20, 20, 10, 10)
    gc.clear()
    assert canvas.find_all() == ()


def test_on_key_rejects_unknown_keys(game_canvas):
    gc, canvas, root = game_canvas
    with pytest.raises(ValueError):
        gc.on_key("Enter", lambda: None)


def test_on_key_fires_callback_on_the_bound_key(game_canvas):
    gc, canvas, root = game_canvas
    calls = []
    gc.on_key("Up", lambda: calls.append(1))

    # A withdrawn window can't hold real keyboard focus, and Tk's key-event
    # delivery depends on it -- deiconify/focus_force here (the real app's
    # game windows are always visible, so this matches production).
    root.deiconify()
    root.focus_force()
    root.update()
    root.event_generate("<Up>", when="now")
    root.update()

    assert calls == [1]
