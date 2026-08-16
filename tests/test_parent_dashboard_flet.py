"""Exercises _ParentController's real PIN-gate, summary, activity, and
reset logic against the real progress store -- with a fake Page standing
in for a live Flet session, same pattern as test_lesson_screen_flet.py."""
from __future__ import annotations

import pytest

from app.ui.app_state_flet import AppState
from app.ui.parent_dashboard_flet import _ParentController


class FakePage:
    def __init__(self) -> None:
        self.update_count = 0
        self.routes_visited: list[str] = []
        self.dialogs_shown: list = []
        self.dialogs_popped = 0

    def update(self) -> None:
        self.update_count += 1

    def go(self, route: str) -> None:
        self.routes_visited.append(route)

    def show_dialog(self, dialog) -> None:
        self.dialogs_shown.append(dialog)

    def pop_dialog(self):
        self.dialogs_popped += 1


@pytest.fixture
def state(tmp_path, monkeypatch):
    import app.config.settings as settings_module

    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    s.settings.child_name = "Avyaan"
    yield s
    s.close()


def test_no_pin_set_shows_summary_directly_with_a_warning(state):
    controller = _ParentController(FakePage(), state)
    controller.build_view()

    assert not hasattr(controller, "pin_field")
    assert "level" in controller.value_texts
    texts = [c.value for c in controller.body.controls if hasattr(c, "value")]
    assert any("No PIN is set" in t for t in texts)


def test_pin_set_shows_pin_step_first_not_summary(state):
    state.settings.set_parent_pin("1234")
    controller = _ParentController(FakePage(), state)
    controller.build_view()

    assert controller.pin_field is not None
    assert controller.value_texts == {}


def test_correct_pin_unlocks_the_summary(state):
    state.settings.set_parent_pin("1234")
    controller = _ParentController(FakePage(), state)
    controller.build_view()

    controller.pin_field.value = "1234"
    controller._submit_pin()

    assert "level" in controller.value_texts
    assert controller.value_texts["child"].value == "Avyaan"


def test_wrong_pin_shows_error_and_stays_locked(state):
    state.settings.set_parent_pin("1234")
    controller = _ParentController(FakePage(), state)
    controller.build_view()

    controller.pin_field.value = "0000"
    controller._submit_pin()

    assert controller.pin_error_text.value == "Incorrect PIN."
    assert controller.pin_field.value == ""
    assert controller.value_texts == {}  # still locked, summary never built


def test_summary_reflects_real_progress(state):
    state.progress.complete_lesson("lesson_01", 3)
    state.progress.award_badge("first_program")
    state.progress.set_level(2)

    controller = _ParentController(FakePage(), state)
    controller.build_view()

    assert controller.value_texts["level"].value == "2"
    assert controller.value_texts["stars"].value == "⭐ 3"
    assert controller.value_texts["lessons"].value == "1"
    assert controller.value_texts["badges"].value == "1"


def test_activity_log_shows_friendly_labels_with_icons(state):
    state.progress.log_event("lesson_01", "lesson_completed", "stars=3")
    state.progress.log_event(None, "hint_used", "some hint")

    controller = _ParentController(FakePage(), state)
    controller.build_view()

    texts = [c.value for c in controller.activity_column.controls]
    assert any("✅" in t and "Completed a lesson" in t and "lesson_01" in t for t in texts)
    assert any("💡" in t and "Used a hint" in t for t in texts)


def test_empty_activity_shows_placeholder_text(state):
    controller = _ParentController(FakePage(), state)
    controller.build_view()

    texts = [c.value for c in controller.activity_column.controls]
    assert any("Nothing yet" in t for t in texts)


def test_reset_progress_shows_a_confirmation_dialog_first(state):
    state.progress.complete_lesson("lesson_01", 3)
    controller = _ParentController(FakePage(), state)
    controller.build_view()

    controller._confirm_reset(None)

    assert len(controller.page.dialogs_shown) == 1
    # nothing actually reset yet -- only confirmed via the dialog's Reset action
    assert "lesson_01" in state.progress.get_completed_lesson_ids()


def test_confirming_reset_clears_progress_and_updates_the_summary(state):
    state.progress.complete_lesson("lesson_01", 3)
    state.progress.award_badge("first_program")
    controller = _ParentController(FakePage(), state)
    controller.build_view()

    controller._do_reset()

    assert state.progress.get_completed_lesson_ids() == []
    assert state.progress.get_badge_ids() == []
    assert controller.value_texts["stars"].value == "⭐ 0"
    assert controller.status_text.value == "Progress has been reset."
    assert controller.page.dialogs_popped == 1


def test_cancelling_reset_leaves_progress_untouched(state):
    state.progress.complete_lesson("lesson_01", 3)
    controller = _ParentController(FakePage(), state)
    controller.build_view()

    controller._cancel_reset()

    assert "lesson_01" in state.progress.get_completed_lesson_ids()
    assert controller.page.dialogs_popped == 1


def test_menu_navigates_to_dashboard(state):
    controller = _ParentController(FakePage(), state)
    controller.build_view()

    controller._on_menu(None)

    assert controller.page.routes_visited == ["/dashboard"]


# -- This Week / Category Mastery cards --------------------------------------
def test_weekly_card_reflects_recent_activity(state):
    state.progress.complete_lesson("lesson_01", 3)
    state.progress.award_badge("first_program")
    state.progress.record_quiz_attempt(9, 10)

    controller = _ParentController(FakePage(), state)
    controller.build_view()

    assert controller.weekly_value_texts["lessons"].value == "1"
    assert controller.weekly_value_texts["stars"].value == "⭐ 3"
    assert controller.weekly_value_texts["quizzes"].value == "1"
    assert controller.weekly_value_texts["badges"].value == "1"
    assert controller.weekly_value_texts["active_days"].value == "1/7"


def test_weekly_card_is_zeroed_with_no_activity(state):
    controller = _ParentController(FakePage(), state)
    controller.build_view()

    assert controller.weekly_value_texts["lessons"].value == "0"
    assert controller.weekly_value_texts["active_days"].value == "0/7"


def test_mastery_card_has_a_row_for_every_category(state):
    controller = _ParentController(FakePage(), state)
    controller.build_view()

    basics_total = len(state.lesson_engine.lessons_in_category("basics"))
    assert set(controller.mastery_texts) == set(state.lesson_engine.categories())
    assert controller.mastery_texts["basics"].value == f"0/{basics_total}"
    assert controller.mastery_bars["basics"].value == 0.0


def test_mastery_card_reflects_completed_lessons(state):
    basics_ids = [lesson.id for lesson in state.lesson_engine.lessons_in_category("basics")]
    for lesson_id in basics_ids:
        state.progress.complete_lesson(lesson_id, 3)

    controller = _ParentController(FakePage(), state)
    controller.build_view()

    assert controller.mastery_texts["basics"].value == f"{len(basics_ids)}/{len(basics_ids)}"
    assert controller.mastery_bars["basics"].value == 1.0


def test_reset_zeroes_the_weekly_and_mastery_cards(state):
    state.progress.complete_lesson("lesson_01", 3)
    controller = _ParentController(FakePage(), state)
    controller.build_view()

    controller._do_reset()

    basics_total = len(state.lesson_engine.lessons_in_category("basics"))
    assert controller.weekly_value_texts["lessons"].value == "0"
    assert controller.mastery_texts["basics"].value == f"0/{basics_total}"
    assert controller.mastery_bars["basics"].value == 0.0
