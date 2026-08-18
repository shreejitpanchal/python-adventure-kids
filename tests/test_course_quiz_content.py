"""Content checks for the "🎓 Python Learning" course's quiz items (the
3rd item within every topic group of every chapter -- a chapter can hold
several independent topics, each with its own quiz, see
app/engine/course_status.py). The non-quiz code lessons are covered by
test_course_lessons.py instead."""
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


@pytest.fixture(scope="module")
def all_quiz_lessons(engine):
    """Every is_quiz lesson across every chapter/topic, in curriculum order."""
    lessons = []
    for category in COURSE_CATEGORIES:
        for lesson in engine.lessons_in_category(category):
            if lesson.is_quiz:
                lessons.append(lesson)
    return lessons


def test_every_chapter_topic_has_exactly_one_quiz(engine, all_quiz_lessons):
    total_topics = 0
    for category in COURSE_CATEGORIES:
        topics = {lesson.topic for lesson in engine.lessons_in_category(category)}
        total_topics += len(topics)
    assert len(all_quiz_lessons) == total_topics


def test_quiz_items_have_concept_tags_for_filtering(all_quiz_lessons):
    for lesson in all_quiz_lessons:
        assert lesson.concept_tags, f"{lesson.id} has no concept_tags to filter its quiz on"


def test_quiz_item_tags_yield_enough_questions_for_a_real_quiz(quiz_engine, all_quiz_lessons):
    for lesson in all_quiz_lessons:
        session = quiz_engine.start_session_for_tags(lesson.concept_tags, count=8)
        assert len(session) == 8, (
            f"{lesson.id}'s concept_tags {lesson.concept_tags} only yield "
            f"{len(session)} questions -- not enough for an 8-question quiz"
        )
