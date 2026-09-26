import asyncio
from types import SimpleNamespace

from app.ui.components import codey_performance_flet as performance
from app.ui.components.codey_avatar_flet import build_codey_avatar
from app.ui.theme_flet import get_preset
from tests.flet_testing import FakePage, NoTaskPage

THEME = get_preset("sunny_light")


def _lesson(category="basics", tags=()):
    return SimpleNamespace(category=category, concept_tags=list(tags))


def test_performance_matches_the_concept_being_taught():
    loop = performance.performance_for("hi\nhi\nhi\n", _lesson("loops"))
    assert loop.face == "🔁" and "3 times" in loop.line and loop.move == "bounce"

    dice = performance.performance_for("You rolled 4", _lesson("games", ["random"]))
    assert dice.face == "🎲" and dice.move == "spin"

    decision = performance.performance_for("You can play!", _lesson("conditionals"))
    assert decision.face == "🚦" and "You can play!" in decision.line

    asked = performance.performance_for("Hi Sam", _lesson("input"))
    assert asked.face == "🙋"

    maths = performance.performance_for("7", _lesson("addition"))
    assert maths.face == "📦" and "7" in maths.line

    hello = performance.performance_for("Hello!", _lesson("basics"))
    assert hello.face == "🗣️" and hello.line == "Python says “Hello!”" and hello.move == "bounce"


def test_quiet_program_and_long_output_are_handled():
    quiet = performance.performance_for("   \n", _lesson("basics"))
    assert quiet.face == "🤐" and quiet.move == "none"
    long = performance.performance_for("x" * 200, _lesson("strings"))
    assert len(long.line) < 100 and long.line.endswith("…”")


def test_error_and_graphical_performances():
    assert performance.error_performance().move == "wobble"
    assert performance.graphical_performance().move == "bounce"


def test_perform_schedules_on_a_real_page_and_no_ops_without_one():
    handle = build_codey_avatar(THEME)
    page = FakePage()
    assert performance.perform(handle, page, performance.error_performance()) is True
    assert len(page.scheduled(performance._perform)) == 1
    assert handle.caption_text.value == "Ready when you are!", "nothing changes until the task runs"
    assert performance.perform(handle, NoTaskPage(), performance.error_performance()) is False


def test_running_the_performance_types_the_line_and_settles_the_disc():
    handle = build_codey_avatar(THEME)
    page = FakePage()
    perf = performance.Performance("🗣️", "Python says “Hi”", "spin")
    asyncio.run(performance._perform(page, handle, perf, delay=0))
    assert handle.face_text.value == "🗣️"
    assert handle.caption_text.value == perf.line
    assert handle.face_container.rotate == 0.0
    assert page.update_count >= len(perf.line) // performance.TYPEWRITER_CHARS_PER_STEP
