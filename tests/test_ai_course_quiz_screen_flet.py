"""Exercises _CourseQuizController for the "🤖 AI & Machine Learning"
course (course=AI_ML_COURSE) -- mirrors test_course_quiz_screen_flet.py's
pattern, confirming pass/fail branching, badge-awarding, and back-nav all
work correctly for a second course's own categories/badge_id/route prefix."""
from __future__ import annotations

import pytest

from app.engine.courses import AI_ML_COURSE
from app.ui.app_state_flet import AppState
from app.ui.course_quiz_screen_flet import _CourseQuizController

_CHAPTER = AI_ML_COURSE.categories[0]


class FakePage:
    def __init__(self) -> None:
        self.routes_visited: list[str] = []

    def update(self) -> None:
        pass

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
def quiz_lesson_id(state):
    return state.lesson_engine.lessons_in_category(_CHAPTER)[2].id


def _answer_all_right(controller) -> None:
    for _ in range(controller.total):
        question = controller.questions[controller.index]
        controller._on_select(question.correct)
        controller._on_next(None)


def _answer_all_wrong(controller) -> None:
    for _ in range(controller.total):
        question = controller.questions[controller.index]
        wrong_index = 0 if question.correct != 0 else 1
        controller._on_select(wrong_index)
        controller._on_next(None)


def test_perfect_score_completes_the_lesson(state, quiz_lesson_id):
    controller = _CourseQuizController(FakePage(), state, quiz_lesson_id, AI_ML_COURSE)
    controller.build_view()

    _answer_all_right(controller)

    assert controller.results_card.visible is True
    assert quiz_lesson_id in state.progress.get_completed_lesson_ids()


def test_failing_score_does_not_complete_the_lesson(state, quiz_lesson_id):
    controller = _CourseQuizController(FakePage(), state, quiz_lesson_id, AI_ML_COURSE)
    controller.build_view()

    _answer_all_wrong(controller)

    assert controller.results_card.visible is True
    assert quiz_lesson_id not in state.progress.get_completed_lesson_ids()


def test_passing_awards_the_ai_ml_badge_once_every_chapter_is_done(state, quiz_lesson_id):
    all_ids = [
        lesson.id for category in AI_ML_COURSE.categories
        for lesson in state.lesson_engine.lessons_in_category(category)
    ]
    for lesson_id in all_ids:
        if lesson_id != quiz_lesson_id:
            state.progress.complete_lesson(lesson_id, 3)

    controller = _CourseQuizController(FakePage(), state, quiz_lesson_id, AI_ML_COURSE)
    controller.build_view()
    _answer_all_right(controller)

    assert AI_ML_COURSE.badge_id in state.progress.get_badge_ids()


def test_back_button_navigates_to_the_ai_course_chapter(state, quiz_lesson_id):
    controller = _CourseQuizController(FakePage(), state, quiz_lesson_id, AI_ML_COURSE)
    controller.build_view()

    controller._on_back(None)

    assert controller.page.routes_visited == [f"/ai-course/{_CHAPTER}"]
