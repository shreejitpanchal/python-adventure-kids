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


def _complete_world(state, world) -> None:
    for category in world.categories:
        for lesson in state.lesson_engine.lessons_in_category(category):
            state.progress.complete_lesson(lesson.id, 3)


def test_boss_mode_starts_straight_away_with_the_worlds_questions(state):
    from app.engine.boss import BOSS_QUESTION_COUNT, boss_tags, world_by_id
    from app.ui.quiz_screen_flet import build_quiz_view
    from tests.flet_testing import one

    world = world_by_id("number_kingdom")
    page = FakePage()
    view = build_quiz_view(page, state, boss_world_id="number_kingdom")
    assert view.route == "/boss/number_kingdom"
    assert one(view, "hero_header").data["title"] == "⚔️ Boss: Number Kingdom"
    assert one(view, "skyline").data["world"] == "number_kingdom"
    assert view.bottom_appbar.data["active"] == "map"
    assert view.bgcolor != state.theme.bg, "the boss fight wears the World's skin"

    controller = _QuizController(page, state, boss=world)
    controller.build_view()
    assert controller.setup_card.visible is False and controller.question_card.visible is True
    assert controller.total == BOSS_QUESTION_COUNT
    tags = boss_tags(state.lesson_engine, world)
    assert all(set(question.concept_tags) & tags for question in controller.questions)


def test_unknown_boss_world_falls_back_to_the_plain_quiz(state):
    from app.ui.quiz_screen_flet import build_quiz_view

    view = build_quiz_view(FakePage(), state, boss_world_id="nowhere")
    assert view.route == "/quiz"


def test_winning_the_boss_awards_its_badge_once_and_a_loss_does_not(state):
    from app.engine.boss import boss_badge_id, world_by_id

    world = world_by_id("word_valley")
    _complete_world(state, world)
    controller = _QuizController(FakePage(), state, boss=world)
    controller.build_view()
    _answer_all_right(controller)
    assert controller.boss_won is True
    assert boss_badge_id(world) in state.progress.get_badge_ids()
    assert controller.confetti.data["fired"] is True
    assert "defeated" in controller.results_text.value

    loss = _QuizController(FakePage(), state, boss=world)
    loss.build_view()
    _answer_all_wrong(loss)
    assert loss.boss_won is False
    assert "shrugged" in loss.results_text.value
    assert loss.confetti.data["fired"] is False

    # A rematch restarts the fight without a setup card.
    loss._on_play_again(None)
    assert loss.setup_card.visible is False and loss.question_card.visible is True and loss.index == 0


def test_a_strong_score_fires_confetti_and_a_weak_one_does_not(state):
    strong = _QuizController(FakePage(), state)
    strong.build_view()
    strong._on_pick_count(5)
    _answer_all_right(strong)
    # FakePage can't schedule tasks, so the burst is applied immediately.
    assert strong.confetti.data["fired"] is True
    assert strong.results_card.visible is True

    weak = _QuizController(FakePage(), state)
    weak.build_view()
    weak._on_pick_count(5)
    _answer_all_wrong(weak)
    assert weak.confetti.data["fired"] is False

    strong._on_play_again(None)
    assert strong.confetti.data["fired"] is False, "play again rewinds the confetti"


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
