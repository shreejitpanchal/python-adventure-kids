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


def test_forward_draws_a_line_from_the_starting_position(game_canvas):
    gc, canvas, root = game_canvas
    shape_id = gc.forward(100)
    coords = canvas.coords(shape_id)
    # Starts inset at (50, 50); heading 0 = facing +x, so straight right.
    assert coords == pytest.approx([50.0, 50.0, 150.0, 50.0])


def test_forward_twice_continues_from_the_new_position(game_canvas):
    gc, canvas, root = game_canvas
    gc.forward(50)
    second_id = gc.forward(30)
    coords = canvas.coords(second_id)
    assert coords == pytest.approx([100.0, 50.0, 130.0, 50.0])


def test_turn_right_rotates_the_heading_clockwise(game_canvas):
    gc, canvas, root = game_canvas
    gc.turn_right(90)
    shape_id = gc.forward(40)
    coords = canvas.coords(shape_id)
    # Heading 90 with y-down screen coords means straight down.
    assert coords == pytest.approx([50.0, 50.0, 50.0, 90.0])


def test_turn_left_rotates_the_heading_counterclockwise(game_canvas):
    gc, canvas, root = game_canvas
    gc.turn_left(90)
    shape_id = gc.forward(40)
    coords = canvas.coords(shape_id)
    assert coords == pytest.approx([50.0, 50.0, 50.0, 10.0])


def test_four_forward_and_turn_right_draws_a_closed_square():
    root = tk.Tk()
    root.withdraw()
    canvas = tk.Canvas(root)
    gc = GameCanvas(canvas, root)
    for _ in range(4):
        gc.forward(100)
        gc.turn_right(90)
    assert (gc._turtle_x, gc._turtle_y) == pytest.approx((50.0, 50.0))
    root.destroy()


def test_draw_line_is_independent_of_turtle_position_and_heading(game_canvas):
    gc, canvas, root = game_canvas
    gc.turn_right(45)  # should have no effect on draw_line
    shape_id = gc.draw_line(0, 0, 10, 10, "blue")
    assert canvas.coords(shape_id) == [0.0, 0.0, 10.0, 10.0]
    assert canvas.itemcget(shape_id, "fill") == "blue"
    # And doesn't move the turtle itself.
    assert (gc._turtle_x, gc._turtle_y) == (50.0, 50.0)


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
