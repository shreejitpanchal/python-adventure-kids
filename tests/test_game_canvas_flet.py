import asyncio

import flet as ft
import flet.canvas as cv
import pytest

from app.games.game_canvas_flet import GameCanvas


class FakePage:
    """Individual Flet controls' own .update() requires them to already be
    attached to a live page tree (it raises otherwise); page.update() has
    no such requirement, which is exactly why GameCanvas calls the latter.
    This stands in for that without needing a real Flet session."""

    def update(self) -> None:
        pass


def make_canvas():
    canvas_control = cv.Canvas(shapes=[])
    container = ft.Container(content=canvas_control, bgcolor="#000000")
    title_text = ft.Text("")
    gc = GameCanvas(canvas_control, container, title_text, FakePage())
    return gc, canvas_control, container, title_text


def test_set_title_updates_title_text():
    gc, canvas, container, title_text = make_canvas()
    gc.set_title("My Game")
    assert title_text.value == "My Game"


def test_set_background_updates_container_bgcolor():
    gc, canvas, container, title_text = make_canvas()
    gc.set_background("black")
    assert container.bgcolor == "black"


def test_draw_rect_adds_a_shape_and_returns_an_id():
    gc, canvas, container, title_text = make_canvas()
    shape_id = gc.draw_rect(10, 20, 30, 40, "green")
    assert isinstance(shape_id, int)
    assert len(canvas.shapes) == 1
    rect = canvas.shapes[0]
    assert (rect.x, rect.y, rect.width, rect.height) == (10, 20, 30, 40)


def test_drawing_two_shapes_gives_distinct_ids():
    gc, canvas, container, title_text = make_canvas()
    a = gc.draw_rect(0, 0, 10, 10)
    b = gc.draw_rect(0, 0, 10, 10)
    assert a != b
    assert len(canvas.shapes) == 2


def test_move_shape_updates_position_relatively():
    gc, canvas, container, title_text = make_canvas()
    shape_id = gc.draw_rect(0, 0, 10, 10)
    gc.move_shape(shape_id, 5, -3)
    assert gc.get_shape_position(shape_id) == (5, -3)


def test_set_shape_position_sets_absolute_position():
    gc, canvas, container, title_text = make_canvas()
    shape_id = gc.draw_rect(0, 0, 10, 10)
    gc.set_shape_position(shape_id, 100, 200)
    assert gc.get_shape_position(shape_id) == (100, 200)


def test_delete_shape_removes_it_from_canvas():
    gc, canvas, container, title_text = make_canvas()
    shape_id = gc.draw_rect(0, 0, 10, 10)
    gc.delete_shape(shape_id)
    assert len(canvas.shapes) == 0
    assert gc.get_shape_position(shape_id) == (0, 0)  # unknown id -> safe default


def test_clear_removes_all_shapes():
    gc, canvas, container, title_text = make_canvas()
    gc.draw_rect(0, 0, 10, 10)
    gc.draw_rect(20, 20, 10, 10)
    gc.clear()
    assert len(canvas.shapes) == 0


def test_forward_draws_a_line_from_the_starting_position():
    gc, canvas, container, title_text = make_canvas()
    shape_id = gc.forward(100)
    assert len(canvas.shapes) == 1
    line = canvas.shapes[0]
    assert (line.x1, line.y1, line.x2, line.y2) == pytest.approx([50.0, 50.0, 150.0, 50.0])
    assert isinstance(shape_id, int)


def test_forward_twice_continues_from_the_new_position():
    gc, canvas, container, title_text = make_canvas()
    gc.forward(50)
    gc.forward(30)
    second_line = canvas.shapes[1]
    assert (second_line.x1, second_line.y1, second_line.x2, second_line.y2) == pytest.approx([100.0, 50.0, 130.0, 50.0])


def test_turn_right_rotates_the_heading_clockwise():
    gc, canvas, container, title_text = make_canvas()
    gc.turn_right(90)
    gc.forward(40)
    line = canvas.shapes[0]
    assert (line.x1, line.y1, line.x2, line.y2) == pytest.approx([50.0, 50.0, 50.0, 90.0])


def test_turn_left_rotates_the_heading_counterclockwise():
    gc, canvas, container, title_text = make_canvas()
    gc.turn_left(90)
    gc.forward(40)
    line = canvas.shapes[0]
    assert (line.x1, line.y1, line.x2, line.y2) == pytest.approx([50.0, 50.0, 50.0, 10.0])


def test_four_forward_and_turn_right_draws_a_closed_square():
    gc, canvas, container, title_text = make_canvas()
    for _ in range(4):
        gc.forward(100)
        gc.turn_right(90)
    assert (gc._turtle_x, gc._turtle_y) == pytest.approx((50.0, 50.0))
    assert len(canvas.shapes) == 4


def test_draw_line_is_independent_of_turtle_position_and_heading():
    gc, canvas, container, title_text = make_canvas()
    gc.turn_right(45)  # should have no effect on draw_line
    gc.draw_line(0, 0, 10, 10, "blue")
    line = canvas.shapes[0]
    assert (line.x1, line.y1, line.x2, line.y2) == (0, 0, 10, 10)
    assert line.paint.color == "blue"
    # And doesn't move the turtle itself.
    assert (gc._turtle_x, gc._turtle_y) == (50.0, 50.0)


def test_draw_circle_adds_a_shape_centered_at_x_y():
    gc, canvas, container, title_text = make_canvas()
    shape_id = gc.draw_circle(100, 120, 15, "red")
    assert isinstance(shape_id, int)
    assert len(canvas.shapes) == 1
    circle = canvas.shapes[0]
    assert (circle.x, circle.y, circle.radius) == (100, 120, 15)
    assert circle.paint.color == "red"


def test_draw_circle_and_draw_rect_ids_dont_collide():
    gc, canvas, container, title_text = make_canvas()
    a = gc.draw_rect(0, 0, 10, 10)
    b = gc.draw_circle(0, 0, 5)
    assert a != b


def test_move_shape_works_for_circles_too():
    gc, canvas, container, title_text = make_canvas()
    shape_id = gc.draw_circle(50, 50, 10)
    gc.move_shape(shape_id, 5, -5)
    assert gc.get_shape_position(shape_id) == (55, 45)


def test_check_collision_true_when_two_rects_overlap():
    gc, canvas, container, title_text = make_canvas()
    a = gc.draw_rect(0, 0, 20, 20)
    b = gc.draw_rect(10, 10, 20, 20)
    assert gc.check_collision(a, b) is True


def test_check_collision_false_when_two_rects_dont_overlap():
    gc, canvas, container, title_text = make_canvas()
    a = gc.draw_rect(0, 0, 10, 10)
    b = gc.draw_rect(100, 100, 10, 10)
    assert gc.check_collision(a, b) is False


def test_check_collision_between_a_circle_and_a_rect():
    gc, canvas, container, title_text = make_canvas()
    ball = gc.draw_circle(20, 20, 10)  # bbox (10,10)-(30,30)
    paddle = gc.draw_rect(25, 25, 40, 10)  # bbox (25,25)-(65,35)
    assert gc.check_collision(ball, paddle) is True

    gc.set_shape_position(ball, 200, 200)
    assert gc.check_collision(ball, paddle) is False


def test_check_collision_touching_edges_does_not_count_as_overlap():
    gc, canvas, container, title_text = make_canvas()
    a = gc.draw_rect(0, 0, 10, 10)
    b = gc.draw_rect(10, 0, 10, 10)  # flush against a's right edge
    assert gc.check_collision(a, b) is False


def test_check_collision_with_an_unknown_shape_id_is_false_not_a_crash():
    gc, canvas, container, title_text = make_canvas()
    a = gc.draw_rect(0, 0, 10, 10)
    assert gc.check_collision(a, 9999) is False


def test_check_collision_ignores_shapes_with_no_tracked_size():
    gc, canvas, container, title_text = make_canvas()
    a = gc.draw_rect(0, 0, 100, 100)
    line_id = gc.draw_line(0, 0, 10, 10)
    assert gc.check_collision(a, line_id) is False


def test_delete_shape_forgets_its_size_for_collision_checks():
    gc, canvas, container, title_text = make_canvas()
    a = gc.draw_rect(0, 0, 10, 10)
    b = gc.draw_rect(0, 0, 10, 10)
    gc.delete_shape(b)
    assert gc.check_collision(a, b) is False


def test_is_key_down_false_before_any_key_down():
    gc, canvas, container, title_text = make_canvas()
    assert gc.is_key_down("Left") is False


def test_key_down_then_is_key_down_true():
    gc, canvas, container, title_text = make_canvas()
    gc.key_down("Left")
    assert gc.is_key_down("Left") is True


def test_key_up_releases_a_held_key():
    gc, canvas, container, title_text = make_canvas()
    gc.key_down("Left")
    gc.key_up("Left")
    assert gc.is_key_down("Left") is False


def test_key_up_on_a_key_never_pressed_is_a_safe_no_op():
    gc, canvas, container, title_text = make_canvas()
    gc.key_up("Right")  # should not raise


def test_key_down_silently_ignores_unrecognized_keys():
    gc, canvas, container, title_text = make_canvas()
    gc.key_down("Enter")  # should not raise -- driven by real keyboard events, not lesson code


def test_is_key_down_rejects_unknown_key():
    gc, canvas, container, title_text = make_canvas()
    with pytest.raises(ValueError):
        gc.is_key_down("Escape")


def test_on_key_rejects_unknown_key():
    gc, canvas, container, title_text = make_canvas()
    with pytest.raises(ValueError):
        gc.on_key("Enter", lambda: None)


def test_on_key_registers_and_trigger_key_fires_it():
    gc, canvas, container, title_text = make_canvas()
    calls = []
    gc.on_key("Up", lambda: calls.append("up"))
    gc.trigger_key("Up")
    assert calls == ["up"]


def test_trigger_key_with_no_handler_is_a_safe_no_op():
    gc, canvas, container, title_text = make_canvas()
    gc.trigger_key("Down")  # should not raise


def test_after_schedules_callback_on_the_running_loop():
    gc, canvas, container, title_text = make_canvas()
    calls = []

    async def scenario():
        gc.after(10, lambda: calls.append("fired"))
        await asyncio.sleep(0.05)

    asyncio.run(scenario())
    assert calls == ["fired"]


def test_cancel_pending_stops_a_scheduled_callback():
    gc, canvas, container, title_text = make_canvas()
    calls = []

    async def scenario():
        gc.after(50, lambda: calls.append("fired"))
        gc.cancel_pending()
        await asyncio.sleep(0.1)

    asyncio.run(scenario())
    assert calls == []


# -- Robot Adventure: grid world ------------------------------------------
def test_place_robot_starts_at_the_given_cell_facing_the_given_direction():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(3, 3)
    gc.place_robot(1, 2, "N")
    assert (gc._robot_col, gc._robot_row) == (1, 2)
    assert gc._robot_facing == "N"
    # A body rect + a facing "nose" circle, drawn on top of the gridlines.
    assert gc._robot_body_id is not None
    assert gc._robot_nose_id is not None


def test_robot_forward_moves_one_cell_in_the_facing_direction():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(3, 3)
    gc.place_robot(0, 0, "E")
    moved = gc.robot_forward()
    assert moved is True
    assert (gc._robot_col, gc._robot_row) == (1, 0)


def test_robot_forward_is_blocked_at_the_grid_edge():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(2, 2)
    gc.place_robot(1, 0, "E")
    assert gc.robot_wall_ahead() is True
    assert gc.robot_forward() is False
    assert (gc._robot_col, gc._robot_row) == (1, 0)


def test_robot_forward_is_blocked_by_an_obstacle():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(3, 1)
    gc.place_obstacle(1, 0)
    gc.place_robot(0, 0, "E")
    assert gc.robot_wall_ahead() is True
    assert gc.robot_forward() is False


def test_robot_forward_is_blocked_by_a_placed_wall_from_either_side():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(3, 1)
    gc.place_wall(0, 0, "E")
    gc.place_robot(0, 0, "E")
    assert gc.robot_wall_ahead() is True

    gc.place_robot(1, 0, "W")
    assert gc.robot_wall_ahead() is True


def test_robot_forward_is_not_blocked_by_an_unrelated_wall():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(3, 1)
    gc.place_wall(1, 0, "E")  # blocks (1,0)<->(2,0), not (0,0)<->(1,0)
    gc.place_robot(0, 0, "E")
    assert gc.robot_wall_ahead() is False
    assert gc.robot_forward() is True


def test_robot_turn_right_cycles_clockwise():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(3, 3)
    gc.place_robot(1, 1, "N")
    order = []
    for _ in range(4):
        order.append(gc._robot_facing)
        gc.robot_turn_right()
    assert order == ["N", "E", "S", "W"]


def test_robot_turn_left_cycles_counterclockwise():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(3, 3)
    gc.place_robot(1, 1, "N")
    order = []
    for _ in range(4):
        order.append(gc._robot_facing)
        gc.robot_turn_left()
    assert order == ["N", "W", "S", "E"]


def test_robot_at_goal_true_only_once_the_robot_reaches_it():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(3, 1)
    gc.place_goal(2, 0)
    gc.place_robot(0, 0, "E")
    assert gc.robot_at_goal() is False
    gc.robot_forward()
    assert gc.robot_at_goal() is False
    gc.robot_forward()
    assert gc.robot_at_goal() is True


def test_robot_at_goal_false_with_no_goal_placed():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(3, 1)
    gc.place_robot(0, 0, "E")
    assert gc.robot_at_goal() is False


def test_coins_are_collected_automatically_on_arrival():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(3, 1)
    gc.place_coin(1, 0)
    gc.place_coin(2, 0)
    gc.place_robot(0, 0, "E")
    assert gc.coins_collected() == 0
    gc.robot_forward()
    assert gc.coins_collected() == 1
    gc.robot_forward()
    assert gc.coins_collected() == 2


def test_a_coin_is_only_collected_once():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(3, 1)
    gc.place_coin(1, 0)
    gc.place_robot(0, 0, "E")
    gc.robot_forward()
    assert gc.coins_collected() == 1
    gc.robot_turn_right()
    gc.robot_turn_right()
    gc.robot_forward()  # back to (0,0)
    gc.robot_turn_right()
    gc.robot_turn_right()
    gc.robot_forward()  # (1,0) again -- coin already gone
    assert gc.coins_collected() == 1


def test_robot_turning_does_not_move_it():
    gc, canvas, container, title_text = make_canvas()
    gc.create_grid(3, 3)
    gc.place_robot(1, 1, "N")
    gc.robot_turn_right()
    gc.robot_turn_left()
    assert (gc._robot_col, gc._robot_row) == (1, 1)


def test_self_rescheduling_after_call_pattern_works():
    """Mirrors the Snake lesson's move_snake() self-scheduling pattern."""
    gc, canvas, container, title_text = make_canvas()
    shape_id = gc.draw_rect(0, 0, 10, 10, "green")
    ticks = []

    def move_snake():
        gc.move_shape(shape_id, 10, 0)
        ticks.append(gc.get_shape_position(shape_id))
        if len(ticks) < 3:
            gc.after(10, move_snake)

    async def scenario():
        move_snake()
        await asyncio.sleep(0.2)

    asyncio.run(scenario())
    assert ticks == [(10, 0), (20, 0), (30, 0)]
