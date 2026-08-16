"""Exercises _QuizController's real quiz flow, focused on the new
"practice these next" recommendation added to the results screen --
missed questions' concept_tags are tracked in-session (never persisted)
and cross-referenced against LessonEngine.recommend_practice_for_tags()."""
from __future__ import annotations

import app.config.settings as settings_module
import pytest

from app.ui.app_state_flet import AppState
from app.ui.quiz_screen_flet import _QuizController


class FakePage:
    def __init__(self) -> None:
        self.routes_visited: list[str] = []

    def update(self) -> None:
        pass

    def go(self, route: str) -> None:
        self.routes_visited.append(route)


@pytest.fixture
def state(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module, "resolve_platform_data_dir", lambda: tmp_path)
    s = AppState()
    yield s
    s.close()


def _answer_all_wrong(controller) -> None:
    for _ in range(controller.total):
        question = controller.questions[controller.index]
        wrong_index = 0 if question.correct != 0 else 1
        controller._on_select(wrong_index)
        controller._on_next(None)


def _answer_all_right(controller) -> None:
    for _ in range(controller.total):
        question = controller.questions[controller.index]
        controller._on_select(question.correct)
        controller._on_next(None)


def test_missing_every_question_tracks_their_tags(state):
    controller = _QuizController(FakePage(), state)
    controller.build_view()
    controller._on_pick_count(5)

    _answer_all_wrong(controller)

    assert len(controller.missed_tags) > 0


def test_a_perfect_score_leaves_no_missed_tags_and_no_recommendations(state):
    controller = _QuizController(FakePage(), state)
    controller.build_view()
    controller._on_pick_count(5)

    _answer_all_right(controller)

    assert controller.missed_tags == set()
    assert controller.practice_heading.visible is False
    assert controller.practice_row.controls == []


def test_results_screen_shows_practice_recommendations_when_tags_are_missed(state):
    controller = _QuizController(FakePage(), state)
    controller.build_view()
    controller._on_pick_count(5)

    _answer_all_wrong(controller)

    assert controller.results_card.visible is True
    if controller.missed_tags:  # real content -- some questions may have no tags
        assert controller.practice_heading.visible is True
        assert len(controller.practice_row.controls) > 0


def test_missed_tags_reset_between_sessions(state):
    controller = _QuizController(FakePage(), state)
    controller.build_view()
    controller._on_pick_count(5)
    _answer_all_wrong(controller)
    assert len(controller.missed_tags) > 0

    controller._on_play_again(None)
    controller._on_pick_count(5)
    assert controller.missed_tags == set()


def test_recommendation_button_navigates_to_the_lesson(state):
    controller = _QuizController(FakePage(), state)
    controller.build_view()
    controller._on_pick_count(5)
    _answer_all_wrong(controller)

    if controller.practice_row.controls:
        controller.practice_row.controls[0].on_click(None)
        assert controller.page.routes_visited[0].startswith("/lesson/")
