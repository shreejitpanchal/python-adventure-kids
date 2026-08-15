"""Exercises _LessonController's real Run flow against the real sandbox,
engine, and progress store -- with a fake Page (records .update()/.go()
calls) standing in for a live Flet session. ft.Control objects don't need
a live session just to have their attributes read/written, so this tests
actual state changes directly, without needing a rendered UI."""
from __future__ import annotations

import asyncio

import flet as ft
import pytest

from app.ui.app_state_flet import AppState
from app.ui.lesson_screen_flet import _LessonController


class FakePage:
    def __init__(self) -> None:
        self.update_count = 0
        self.routes_visited: list[str] = []

    def update(self) -> None:
        self.update_count += 1

    def go(self, route: str) -> None:
        self.routes_visited.append(route)


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


@pytest.fixture
def controller(state):
    lesson = state.lesson_engine.get("lesson_01")
    return _LessonController(FakePage(), state, lesson)


class FakeSoundPlayer:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def play(self, name: str, settings) -> None:
        self.calls.append(name)


def test_view_builds_with_starter_code_preloaded(controller):
    view = controller.build_view()
    assert view.route == "/lesson/lesson_01"
    assert controller.editor.value == 'print("Hello!")'
    assert controller.output_text.value == "Press RUN to see what happens!"
    assert controller.reward_card.visible is False


def test_correct_code_completes_the_lesson(controller, state):
    controller.build_view()
    asyncio.run(controller._on_run(None))

    assert controller.output_text.value == "Hello!\n"
    assert controller.output_text.color == state.theme.success
    assert controller.reward_card.visible is True
    assert "⭐⭐⭐" in controller.reward_text.value
    assert "First Program" in controller.badge_text.value

    assert "lesson_01" in state.progress.get_completed_lesson_ids()
    assert "first_program" in state.progress.get_badge_ids()
    assert state.progress.get_summary().current_lesson_id == "lesson_02"


# -- sound effects on lesson success ---------------------------------------
def test_plain_success_plays_only_the_success_chime(state):
    fake_player = FakeSoundPlayer()
    state.sound_player = fake_player
    lesson = state.lesson_engine.get("lesson_02")  # badge: null, no level-up from one small completion
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    controller.editor.value = "print(7)"

    asyncio.run(controller._on_run(None))

    assert fake_player.calls == ["success_chime"]


def test_badge_award_plays_the_badge_unlock_sound_alongside_success(controller, state):
    fake_player = FakeSoundPlayer()
    state.sound_player = fake_player
    controller.build_view()  # lesson_01 awards the first_program badge

    asyncio.run(controller._on_run(None))

    assert fake_player.calls == ["success_chime", "badge_unlock"]


def test_leveling_up_plays_the_level_up_sound_instead_of_the_plain_chime(state):
    fake_player = FakeSoundPlayer()
    state.sound_player = fake_player
    state.progress.add_xp(95)  # 5 XP short of the level 1->2 boundary (100)
    lesson = state.lesson_engine.get("lesson_02")  # badge: null, isolates the level-up sound
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    controller.editor.value = "print(7)"

    asyncio.run(controller._on_run(None))

    assert fake_player.calls == ["level_up"]


def test_no_sound_player_attached_does_not_crash_on_success(controller, state):
    assert state.sound_player is None  # default in every test that doesn't attach one
    controller.build_view()

    asyncio.run(controller._on_run(None))  # should not raise

    assert "lesson_01" in state.progress.get_completed_lesson_ids()


def test_syntax_error_shows_friendly_message_with_line_number(controller, state):
    controller.build_view()
    controller.editor.value = 'print("Hello!"'  # missing closing paren
    asyncio.run(controller._on_run(None))

    assert "isn't quite right" in controller.output_text.value
    assert "line 1" in controller.output_text.value
    assert controller.output_text.color == state.theme.danger
    assert controller.details_button.visible is True
    assert "SyntaxError" in controller.details_text.value
    assert controller.reward_card.visible is False
    assert "lesson_01" not in state.progress.get_completed_lesson_ids()


def test_wrong_output_does_not_complete_the_lesson(controller, state):
    controller.build_view()
    controller.editor.value = 'print("Goodbye!")'
    asyncio.run(controller._on_run(None))

    assert "Goodbye!" in controller.output_text.value
    assert controller.output_text.color == state.theme.warning
    assert controller.reward_card.visible is False
    assert "lesson_01" not in state.progress.get_completed_lesson_ids()


def test_blocked_import_shows_blocked_message(controller, state):
    controller.build_view()
    controller.editor.value = "import os\nprint('Hello!')"
    asyncio.run(controller._on_run(None))

    assert controller.output_text.value.startswith("🚫")
    assert controller.reward_card.visible is False
    assert "lesson_01" not in state.progress.get_completed_lesson_ids()


def test_reset_restores_starter_code_and_clears_output(controller):
    controller.build_view()
    controller.editor.value = "something else entirely"
    controller.output_text.value = "some previous output"
    controller.reward_card.visible = True

    controller._on_reset(None)

    assert controller.editor.value == 'print("Hello!")'
    assert controller.output_text.value == "Press RUN to see what happens!"
    assert controller.reward_card.visible is False


def test_hint_cycles_through_lesson_hints(controller, state):
    controller.build_view()
    lesson = state.lesson_engine.get("lesson_01")

    controller._on_hint(None)
    assert controller.hint_text.value == f"💡 {lesson.hints[0]}"

    controller._on_hint(None)
    assert controller.hint_text.value == f"💡 {lesson.hints[1]}"


def test_menu_cancels_any_in_flight_run_and_navigates_home(controller):
    controller.build_view()
    controller._on_menu(None)
    assert controller.page.routes_visited == ["/dashboard"]


def test_second_run_does_not_double_award_stars_or_badges(controller, state):
    controller.build_view()
    asyncio.run(controller._on_run(None))
    asyncio.run(controller._on_run(None))

    summary = state.progress.get_summary()
    assert summary.total_stars == 3  # not 6
    assert state.progress.get_badge_ids() == ["first_program"]


# -- graphical lessons (Snake, folded in during Phase 6) ---------------------

@pytest.fixture
def graphical_controller(state):
    lesson = state.lesson_engine.get("lesson_17")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    return controller


def test_graphical_view_includes_a_game_panel(graphical_controller):
    assert graphical_controller._game_canvas_control is not None
    assert graphical_controller._game_container is not None


def test_non_graphical_view_has_no_game_panel(controller):
    controller.build_view()
    assert not hasattr(controller, "_game_canvas_control")


def test_graphical_lesson_run_draws_shape_and_completes(graphical_controller, state):
    asyncio.run(graphical_controller._on_run(None))

    assert "running" in graphical_controller.output_text.value.lower()
    assert graphical_controller.output_text.color == state.theme.success
    assert graphical_controller.reward_card.visible is True
    assert "lesson_17" in state.progress.get_completed_lesson_ids()
    assert len(graphical_controller._game_canvas_control.shapes) == 1


def test_graphical_lesson_blocked_import(graphical_controller):
    graphical_controller.editor.value = "import os\ngame.set_background('black')"
    asyncio.run(graphical_controller._on_run(None))
    assert graphical_controller.output_text.value.startswith("🚫")
    assert graphical_controller.reward_card.visible is False


def test_graphical_lesson_runtime_error_shows_friendly_message(graphical_controller, state):
    graphical_controller.editor.value = "game.draw_rect(1, 2, 3, 4)\nprint(1 / 0)"
    asyncio.run(graphical_controller._on_run(None))
    assert graphical_controller.output_text.color == state.theme.danger
    assert "lesson_17" not in state.progress.get_completed_lesson_ids()


def test_graphical_lesson_while_loop_is_blocked(graphical_controller):
    graphical_controller.editor.value = "while True:\n    pass"
    asyncio.run(graphical_controller._on_run(None))
    assert graphical_controller.output_text.value.startswith("🚫")
    assert "freeze" in graphical_controller.output_text.value


def test_dpad_key_triggers_a_lesson_registered_on_key_handler(graphical_controller):
    graphical_controller.editor.value = (
        'snake = game.draw_rect(0, 0, 10, 10, "green")\n'
        "def go_up():\n"
        "    game.move_shape(snake, 0, -10)\n"
        "game.on_key(\"Up\", go_up)\n"
    )
    asyncio.run(graphical_controller._on_run(None))
    graphical_controller._trigger_game_key("Up")

    shape_id = next(iter(graphical_controller.game_canvas._shapes))
    assert graphical_controller.game_canvas.get_shape_position(shape_id) == (0, -10)


def test_lesson_18_self_scheduling_move_pattern_runs_without_crashing(state):
    lesson = state.lesson_engine.get("lesson_18")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()

    asyncio.run(controller._on_run(None))

    assert controller.reward_card.visible is True
    assert "lesson_18" in state.progress.get_completed_lesson_ids()


def test_reset_on_graphical_lesson_clears_canvas_and_cancels_pending_timers(graphical_controller):
    asyncio.run(graphical_controller._on_run(None))
    assert len(graphical_controller._game_canvas_control.shapes) == 1

    graphical_controller._on_reset(None)

    assert len(graphical_controller._game_canvas_control.shapes) == 0
    assert graphical_controller.reward_card.visible is False


def test_graphical_view_wraps_the_game_panel_in_a_keyboard_listener(graphical_controller):
    view = graphical_controller.build_view()

    def find_keyboard_listener(control):
        if isinstance(control, ft.KeyboardListener):
            return control
        children = getattr(control, "controls", None) or ([control.content] if getattr(control, "content", None) else [])
        for child in children:
            if child is not None:
                found = find_keyboard_listener(child)
                if found is not None:
                    return found
        return None

    listener = find_keyboard_listener(view)
    assert listener is not None
    assert listener.on_key_down == graphical_controller._on_key_down
    assert listener.on_key_up == graphical_controller._on_key_up


def test_key_down_triggers_discrete_handler_and_marks_the_key_held(graphical_controller):
    graphical_controller.editor.value = (
        'snake = game.draw_rect(0, 0, 10, 10, "green")\n'
        "def go_up():\n"
        "    game.move_shape(snake, 0, -10)\n"
        "game.on_key(\"Up\", go_up)\n"
    )
    asyncio.run(graphical_controller._on_run(None))

    graphical_controller._on_key_down(ft.KeyDownEvent(name="key_down", control=None, key="Arrow Up"))

    shape_id = next(iter(graphical_controller.game_canvas._shapes))
    assert graphical_controller.game_canvas.get_shape_position(shape_id) == (0, -10)
    assert graphical_controller.game_canvas.is_key_down("Up") is True


def test_key_up_releases_the_held_key(graphical_controller):
    asyncio.run(graphical_controller._on_run(None))
    graphical_controller._on_key_down(ft.KeyDownEvent(name="key_down", control=None, key="Arrow Left"))
    assert graphical_controller.game_canvas.is_key_down("Left") is True

    graphical_controller._on_key_up(ft.KeyUpEvent(name="key_up", control=None, key="Arrow Left"))
    assert graphical_controller.game_canvas.is_key_down("Left") is False


def test_unmapped_key_is_ignored_by_key_down_and_key_up(graphical_controller):
    asyncio.run(graphical_controller._on_run(None))
    graphical_controller._on_key_down(ft.KeyDownEvent(name="key_down", control=None, key="Enter"))
    graphical_controller._on_key_up(ft.KeyUpEvent(name="key_up", control=None, key="Enter"))  # should not raise


# -- Robot Adventure: requires_goal_reached ----------------------------------
@pytest.fixture
def robot_controller(state):
    lesson = state.lesson_engine.get("lesson_440")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    return controller


def test_reaching_the_goal_completes_the_lesson(robot_controller, state):
    asyncio.run(robot_controller._on_run(None))

    assert robot_controller.output_text.color == state.theme.success
    assert robot_controller.reward_card.visible is True
    assert "lesson_440" in state.progress.get_completed_lesson_ids()


def test_running_without_reaching_the_goal_shows_a_warning_and_does_not_complete(robot_controller, state):
    # Passes ast_contains (still calls create_grid/place_robot/robot_forward)
    # but only moves one square, short of the goal at column 2.
    robot_controller.editor.value = (
        'game.set_background("black")\n'
        "game.create_grid(3, 1)\n"
        "game.place_goal(2, 0)\n"
        'game.place_robot(0, 0, "E")\n'
        "game.robot_forward()\n"
    )
    asyncio.run(robot_controller._on_run(None))

    assert "didn't reach the goal" in robot_controller.output_text.value
    assert robot_controller.output_text.color == state.theme.warning
    assert robot_controller.reward_card.visible is False
    assert "lesson_440" not in state.progress.get_completed_lesson_ids()


def test_a_lesson_without_requires_goal_reached_ignores_robot_state(graphical_controller):
    """lesson_17 (Snake) has requires_goal_reached=False (the default) --
    confirms the new mission_ok check doesn't affect non-Robot-Adventure
    graphical lessons at all."""
    assert graphical_controller.lesson.requires_goal_reached is False
    asyncio.run(graphical_controller._on_run(None))
    assert graphical_controller.reward_card.visible is True


# -- Codey avatar wiring (phase 8) --------------------------------------------

def test_codey_starts_idle(controller):
    controller.build_view()
    assert controller._codey.caption_text.value == "Ready when you are!"


def test_codey_shows_success_when_the_lesson_passes(controller):
    controller.build_view()
    asyncio.run(controller._on_run(None))
    assert controller._codey.caption_text.value == "Awesome job!"


def test_codey_shows_warning_on_wrong_output(controller):
    controller.build_view()
    controller.editor.value = 'print("Goodbye!")'
    asyncio.run(controller._on_run(None))
    assert controller._codey.caption_text.value == "So close -- try again!"


def test_codey_shows_error_on_a_runtime_exception(controller):
    controller.build_view()
    controller.editor.value = 'print("Hello!"'  # syntax error
    asyncio.run(controller._on_run(None))
    assert controller._codey.caption_text.value == "Uh oh, something broke!"


def test_codey_shows_blocked_on_a_disallowed_import(controller):
    controller.build_view()
    controller.editor.value = "import os\nprint('Hello!')"
    asyncio.run(controller._on_run(None))
    assert controller._codey.caption_text.value == "Can't do that one yet!"


def test_codey_returns_to_idle_on_reset(controller):
    controller.build_view()
    asyncio.run(controller._on_run(None))
    assert controller._codey.caption_text.value == "Awesome job!"

    controller._on_reset(None)
    assert controller._codey.caption_text.value == "Ready when you are!"


def test_codey_shows_success_on_a_completed_graphical_lesson(graphical_controller):
    asyncio.run(graphical_controller._on_run(None))
    assert graphical_controller._codey.caption_text.value == "Awesome job!"


def test_codey_shows_error_on_a_graphical_runtime_exception(graphical_controller, state):
    graphical_controller.editor.value = "game.draw_rect(1, 2, 3, 4)\nprint(1 / 0)"
    asyncio.run(graphical_controller._on_run(None))
    assert graphical_controller._codey.caption_text.value == "Uh oh, something broke!"


def test_codey_shows_blocked_on_a_graphical_disallowed_construct(graphical_controller):
    graphical_controller.editor.value = "while True:\n    pass"
    asyncio.run(graphical_controller._on_run(None))
    assert graphical_controller._codey.caption_text.value == "Can't do that one yet!"
