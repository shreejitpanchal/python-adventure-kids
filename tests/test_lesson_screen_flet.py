"""Exercises _LessonController's real Run flow against the real sandbox,
engine, and progress store -- with a fake Page (records .update()/.go()
calls) standing in for a live Flet session. ft.Control objects don't need
a live session just to have their attributes read/written, so this tests
actual state changes directly, without needing a rendered UI."""
from __future__ import annotations

import asyncio

import flet as ft
import pytest

from app.engine.categories import get_category_meta
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


# -- inline reward card: Onward / Next Lesson (no popup) --------------------
def test_success_shows_inline_not_a_popup_with_no_next_lesson_in_a_1_level_category(controller):
    controller.build_view()
    asyncio.run(controller._on_run(None))

    # lesson_01 is the only lesson in "basics" -- nothing to advance to.
    assert controller.reward_card.visible is True
    assert controller.next_lesson_button.visible is False


def test_next_lesson_button_appears_when_the_category_has_a_further_level(state):
    lesson = state.lesson_engine.get("lesson_03")  # addition level 1
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    controller.editor.value = "print(7 + 5)"
    asyncio.run(controller._on_run(None))

    assert controller.reward_card.visible is True
    assert controller.next_lesson_button.visible is True
    assert controller._next_in_category_id is not None
    next_lesson = state.lesson_engine.get(controller._next_in_category_id)
    assert next_lesson.category == "addition"
    assert next_lesson.category_level == 2


def test_clicking_next_lesson_navigates_to_the_next_level_in_the_same_category(state):
    lesson = state.lesson_engine.get("lesson_03")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    controller.editor.value = "print(7 + 5)"
    asyncio.run(controller._on_run(None))

    next_id = controller._next_in_category_id
    controller._on_next_lesson(None)
    assert controller.page.routes_visited == [f"/lesson/{next_id}"]


def test_clicking_next_mission_navigates_directly_to_the_next_mission_lesson(state, controller):
    """lesson_01 ("Meet Python") is the one-time "basics" intro -- its
    next_after() mission is lesson_02, the first level of the Today's
    Mission round-robin. Clicking Next Mission should go straight there,
    not through the Dashboard."""
    controller.build_view()
    asyncio.run(controller._on_run(None))

    next_mission = state.lesson_engine.next_after("lesson_01")
    assert next_mission.id == "lesson_02"
    controller._on_continue(None)
    assert controller.page.routes_visited == ["/lesson/lesson_02"]


def test_next_mission_caption_previews_the_upcoming_mission(controller, state):
    controller.build_view()
    asyncio.run(controller._on_run(None))

    next_mission = state.lesson_engine.next_after("lesson_01")
    meta = get_category_meta(next_mission.category)
    assert controller.next_mission_caption.value == f"{meta.icon} {meta.title} — Level {next_mission.category_level}"


def test_next_mission_falls_back_to_dashboard_when_todays_mission_is_finished(state):
    """lesson_739 is the last lesson in main_path_lessons() -- next_after()
    returns None for it, so Next Mission has nowhere direct to send the
    child and should fall back to the Dashboard, same as the old Onward
    button always did."""
    lesson = state.lesson_engine.get("lesson_739")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    controller.editor.value = (
        'def class_average(students):\n'
        '    total = 0\n'
        '    count = 0\n'
        '    for name, scores in students:\n'
        '        for s in scores:\n'
        '            total += s\n'
        '            count += 1\n'
        '    return total / count\n\n'
        'students = [("Ana", [80, 90]), ("Ben", [70, 60, 100]), ("Cara", [90, 90, 90, 90, 90])]\n'
        'print(class_average(students))'
    )
    asyncio.run(controller._on_run(None))

    assert state.lesson_engine.next_after("lesson_739") is None
    assert controller.next_mission_caption.value == "You've completed Today's Mission! 🎉"
    controller._on_continue(None)
    assert controller.page.routes_visited == ["/dashboard"]


def test_next_level_caption_previews_the_next_level(state):
    lesson = state.lesson_engine.get("lesson_03")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    controller.editor.value = "print(7 + 5)"
    asyncio.run(controller._on_run(None))

    next_in_category = state.lesson_engine.get(controller._next_in_category_id)
    meta = get_category_meta(next_in_category.category)
    assert controller.next_lesson_caption.value == f"{meta.icon} {meta.title} — Level {next_in_category.category_level}"


def test_course_lesson_has_no_next_mission_captions(state):
    """Course lessons keep the original Onward/Next Lesson pair -- the
    Next Mission/Next Level captions only exist for Today's Mission
    lessons (see _build_reward_card())."""
    lesson = state.lesson_engine.get("course_intro_setup_1")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    assert controller.next_mission_caption is None
    assert controller.next_lesson_caption is None


# -- course-chapter-aware navigation (course_* categories only) -------------
def test_course_lesson_onward_goes_to_its_chapter_not_the_dashboard(state):
    lesson = state.lesson_engine.get("course_intro_setup_1")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    controller.editor.value = 'print("Hello, world!")'
    asyncio.run(controller._on_run(None))

    controller._on_continue(None)
    assert controller.page.routes_visited == ["/course/course_intro_setup"]


def test_course_lesson_next_lesson_goes_to_the_next_code_item(state):
    lesson = state.lesson_engine.get("course_intro_setup_1")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    controller.editor.value = 'print("Hello, world!")'
    asyncio.run(controller._on_run(None))

    next_id = controller._next_in_category_id
    assert next_id == "course_intro_setup_2"
    controller._on_next_lesson(None)
    assert controller.page.routes_visited == [f"/lesson/{next_id}"]


def test_course_lesson_next_lesson_routes_to_the_quiz_when_the_next_item_is_a_quiz(state):
    state.progress.complete_lesson("course_intro_setup_1", 2)
    lesson = state.lesson_engine.get("course_intro_setup_2")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    controller.editor.value = (
        '# My About Me program\n'
        'print("My name is Alex")\n'
        'print("I am learning Python!")\n'
        'print("Python is fun!")'
    )
    asyncio.run(controller._on_run(None))

    next_id = controller._next_in_category_id
    assert next_id == "course_intro_setup_3"
    controller._on_next_lesson(None)
    assert controller.page.routes_visited == [f"/course-quiz/{next_id}"]


def test_course_lesson_next_lesson_is_topic_scoped_not_blocked_by_sibling_topics(state):
    """Regression guard for the exact bug next_topic_item() was written to
    fix: completing Sets' first item (skipping Lists/Tuples/Dictionaries
    entirely) must surface Sets' second item as "next", not None -- the
    old whole-category next_unlocked_in_category() would have required
    every earlier category_level (i.e. all of Lists/Tuples/Dictionaries)
    done first, even though topics are supposed to be independent."""
    lesson = state.lesson_engine.get("course_sets_1")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    controller.editor.value = 'colors = {"red", "green", "blue", "red", "yellow"}\nprint(len(colors))\nprint(sorted(colors))'
    asyncio.run(controller._on_run(None))

    assert controller._next_in_category_id == "course_sets_2"


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


def test_wrong_output_does_not_complete_the_lesson(state):
    # lesson_02 (not the shared lesson_01 controller fixture): lesson_01's
    # very first "Meet Python" challenge deliberately accepts any print()
    # output now (see its expected_output_pattern), so it's no longer a
    # lesson where a "wrong" answer exists -- lesson_02 still does exact
    # output matching and exercises the same warning/no-completion path.
    lesson = state.lesson_engine.get("lesson_02")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    asyncio.run(controller._on_run(None))  # unedited starter prints 5, not the challenge's 7

    assert "5" in controller.output_text.value
    assert controller.output_text.color == state.theme.warning
    assert controller.reward_card.visible is False
    assert "lesson_02" not in state.progress.get_completed_lesson_ids()


def test_meet_python_accepts_any_message_inside_print(controller, state):
    """lesson_01's whole point is teaching print() itself, not memorizing
    "Hello!" -- any text a kid types inside the quotes should complete it,
    as long as they still used print() (see ast_contains) and it runs
    without an error."""
    controller.build_view()
    controller.editor.value = 'print("Dogs are the best!")'
    asyncio.run(controller._on_run(None))

    assert "Dogs are the best!" in controller.output_text.value
    assert controller.output_text.color == state.theme.success
    assert controller.reward_card.visible is True
    assert "lesson_01" in state.progress.get_completed_lesson_ids()


def test_meet_python_still_requires_using_print(controller, state):
    controller.build_view()
    controller.editor.value = 'message = "Hello!"'
    asyncio.run(controller._on_run(None))

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
    assert controller.page.routes_visited == ["/hub"]


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


# -- Practice Quest -----------------------------------------------------------
def test_practice_quest_appears_after_repeated_failures_when_tags_overlap(state):
    state.lesson_engine.get("lesson_10").concept_tags = ["conditionals"]
    state.lesson_engine.get("lesson_09").concept_tags = ["conditionals"]

    lesson = state.lesson_engine.get("lesson_10")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()

    for _ in range(3):
        controller.editor.value = 'print("nope")'
        asyncio.run(controller._on_run(None))

    assert controller.practice_quest_container.visible is True
    assert len(controller.practice_quest_row.controls) >= 1


def test_practice_quest_does_not_appear_before_the_failure_threshold(state):
    state.lesson_engine.get("lesson_10").concept_tags = ["conditionals"]
    state.lesson_engine.get("lesson_09").concept_tags = ["conditionals"]

    lesson = state.lesson_engine.get("lesson_10")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()

    controller.editor.value = 'print("nope")'
    asyncio.run(controller._on_run(None))
    controller.editor.value = 'print("nope")'
    asyncio.run(controller._on_run(None))

    assert controller.practice_quest_container.visible is False


def test_practice_quest_does_not_appear_without_matching_tags(state):
    lesson = state.lesson_engine.get("lesson_10")
    lesson.concept_tags = []
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()

    for _ in range(3):
        controller.editor.value = 'print("nope")'
        asyncio.run(controller._on_run(None))

    assert controller.practice_quest_container.visible is False


def test_dismissing_the_practice_quest_hides_it(state):
    state.lesson_engine.get("lesson_10").concept_tags = ["conditionals"]
    state.lesson_engine.get("lesson_09").concept_tags = ["conditionals"]

    lesson = state.lesson_engine.get("lesson_10")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()

    for _ in range(3):
        controller.editor.value = 'print("nope")'
        asyncio.run(controller._on_run(None))
    assert controller.practice_quest_container.visible is True

    controller._dismiss_practice_quest(None)
    assert controller.practice_quest_container.visible is False


def test_succeeding_hides_a_previously_shown_practice_quest(state):
    state.lesson_engine.get("lesson_10").concept_tags = ["conditionals"]
    state.lesson_engine.get("lesson_09").concept_tags = ["conditionals"]

    lesson = state.lesson_engine.get("lesson_10")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()

    for _ in range(3):
        controller.editor.value = 'print("nope")'
        asyncio.run(controller._on_run(None))
    assert controller.practice_quest_container.visible is True

    # lesson_10's starter_code (age = 9) doesn't itself satisfy the
    # challenge -- it needs an actual solution to succeed.
    controller.editor.value = (
        "age = 5\nif age >= 8:\n    print(\"You can play!\")\nelse:\n    print(\"You are too young!\")"
    )
    asyncio.run(controller._on_run(None))
    assert controller.practice_quest_container.visible is False


# -- Codey avatar wiring (phase 8) --------------------------------------------

def test_codey_starts_idle(controller):
    controller.build_view()
    assert controller._codey.caption_text.value == "Ready when you are!"


def test_codey_shows_success_when_the_lesson_passes(controller):
    controller.build_view()
    asyncio.run(controller._on_run(None))
    assert controller._codey.caption_text.value == "Awesome job!"


def test_codey_shows_warning_on_wrong_output(state):
    # lesson_02, not the shared lesson_01 controller fixture -- see
    # test_wrong_output_does_not_complete_the_lesson's comment above.
    lesson = state.lesson_engine.get("lesson_02")
    controller = _LessonController(FakePage(), state, lesson)
    controller.build_view()
    asyncio.run(controller._on_run(None))  # unedited starter prints 5, not the challenge's 7
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
