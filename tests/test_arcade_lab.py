"""Content checks for the Flet-only Arcade Lab track: each lesson's
example_code must run cleanly against a real Flet GameCanvas (in-process,
same execution path lesson_screen_flet.py uses for graphical lessons) and
satisfy its own ast_contains. Unlike Creative Arts, this track has no CTk
equivalent -- game.is_key_down()/check_collision()/draw_circle() only
exist on the Flet GameCanvas, per the Flet-only decision for phase 11."""
import asyncio
import textwrap

import flet as ft
import flet.canvas as cv
import pytest

from app.engine.lesson_engine import LessonEngine
from app.engine.validator import validate_ast_contains
from app.games.game_canvas_flet import GameCanvas
from app.sandbox.inprocess_runner import run_code

ARCADE_IDS = [f"arcade_{i:02d}" for i in range(1, 6)]

# Lessons that schedule a repeating game.after() tick loop -- need a real
# running asyncio loop and a short sleep to let at least one tick fire.
SELF_SCHEDULING_IDS = ["arcade_02", "arcade_03", "arcade_04", "arcade_05"]


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


def _run(code: str, game: GameCanvas):
    return run_code(textwrap.dedent(code).strip(), game=game, disallow_while=True)


async def _run_and_tick(code: str, game: GameCanvas):
    result = _run(code, game=game)
    await asyncio.sleep(0.1)
    game.cancel_pending()
    return result


def test_all_five_arcade_lab_lessons_are_registered(engine):
    lessons = engine.lessons_in_category("arcade_lab")
    assert {lesson.id for lesson in lessons} == set(ARCADE_IDS)
    assert sorted(lesson.category_level for lesson in lessons) == list(range(1, 6))


@pytest.mark.parametrize("lesson_id", ARCADE_IDS)
def test_is_a_bonus_graphical_level_with_ast_contains_set(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert lesson.main_path is False
    assert lesson.graphical is True
    assert lesson.category == "arcade_lab"
    assert lesson.ast_contains, f"{lesson_id} should declare ast_contains"


@pytest.mark.parametrize("lesson_id", ARCADE_IDS)
def test_example_code_satisfies_its_own_ast_contains(engine, lesson_id):
    lesson = engine.get(lesson_id)
    assert validate_ast_contains(lesson.example_code, lesson.ast_contains) is True


def test_arcade_01_draws_a_paddle_and_a_ball(engine):
    lesson = engine.get("arcade_01")
    game = make_game_canvas()
    result = _run(lesson.example_code, game)
    assert result.success is True, result.stderr
    assert len(game._shapes) == 2


@pytest.mark.parametrize("lesson_id", SELF_SCHEDULING_IDS)
def test_self_scheduling_lessons_run_and_tick_without_crashing(engine, lesson_id):
    lesson = engine.get(lesson_id)
    game = make_game_canvas()
    result = asyncio.run(_run_and_tick(lesson.example_code, game))
    assert result.success is True, result.stderr


def test_arcade_02_bounce_logic_actually_reverses_direction_at_the_wall():
    # Same shape/logic as the shipped lesson, but starting the ball right
    # at the right-hand wall so a real bounce is observable within a short
    # sleep -- the shipped lesson starts mid-screen, which wouldn't reach a
    # wall inside a fast test's sleep window.
    code = '''
        game.set_background("black")
        ball = game.draw_circle(348, 140, 8, "yellow")
        dx = 4

        def move_ball():
            global dx
            x, y = game.get_shape_position(ball)
            if x <= 8 or x >= 352:
                dx = -dx
            game.move_shape(ball, dx, 0)
            game.after(20, move_ball)

        move_ball()
    '''
    game = make_game_canvas()

    async def scenario():
        result = _run(code, game)
        assert result.success is True, result.stderr
        await asyncio.sleep(0.1)
        game.cancel_pending()

    asyncio.run(scenario())
    shape_id = next(iter(game._shapes))
    x, _y = game.get_shape_position(shape_id)
    # Started at 348 already moving toward the wall (352) -- if the bounce
    # never fired, x would keep climbing past 352; a real bounce sends it
    # back down below where it started.
    assert x < 348


def test_arcade_05_collision_logic_reverses_the_ball_when_it_hits_the_paddle():
    # Same collision logic as the shipped lesson, ball starting close
    # enough to the paddle that a collision (and bounce) happens within a
    # short sleep window.
    code = '''
        game.set_background("black")
        paddle = game.draw_rect(140, 250, 80, 10, "white")
        ball = game.draw_circle(180, 244, 8, "yellow")
        dy = 4

        def move_ball():
            global dy
            if game.check_collision(ball, paddle):
                dy = -dy
            game.move_shape(ball, 0, dy)
            game.after(20, move_ball)

        move_ball()
    '''
    game = make_game_canvas()

    async def scenario():
        result = _run(code, game)
        assert result.success is True, result.stderr
        await asyncio.sleep(0.1)
        game.cancel_pending()

    asyncio.run(scenario())
    ids = list(game._shapes)
    ball_id = ids[1]  # paddle drawn first, then ball
    _x, y = game.get_shape_position(ball_id)
    # Ball starts at y=244 (already overlapping the paddle's top edge at
    # y=250) heading down -- if the collision never fired, y would keep
    # climbing past the paddle; a real bounce sends it back up.
    assert y < 244
