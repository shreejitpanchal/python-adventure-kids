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
