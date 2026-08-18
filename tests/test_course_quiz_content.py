"""Content checks for the "🎓 Python Learning" course's 6 quiz items (the
category_level 3 lesson in each chapter) -- the 12 code lessons are covered
by test_course_lessons.py instead."""
import pytest

from app.engine.categories import COURSE_CATEGORIES
from app.engine.lesson_engine import LessonEngine
from app.engine.quiz_engine import QuizEngine


@pytest.fixture(scope="module")
def engine():
    return LessonEngine()


@pytest.fixture(scope="module")
def quiz_engine():
    return QuizEngine()


def _quiz_lesson(engine, category):
    return engine.lessons_in_category(category)[2]


@pytest.mark.parametrize("category", COURSE_CATEGORIES)
def test_quiz_item_has_concept_tags_for_filtering(engine, category):
    lesson = _quiz_lesson(engine, category)
    assert lesson.is_quiz is True
    assert lesson.concept_tags, f"{lesson.id} has no concept_tags to filter its quiz on"


@pytest.mark.parametrize("category", COURSE_CATEGORIES)
def test_quiz_item_tags_yield_enough_questions_for_a_real_quiz(engine, quiz_engine, category):
    lesson = _quiz_lesson(engine, category)
    session = quiz_engine.start_session_for_tags(lesson.concept_tags, count=8)
    assert len(session) == 8, (
        f"{lesson.id}'s concept_tags {lesson.concept_tags} only yield "
        f"{len(session)} questions -- not enough for an 8-question quiz"
    )
