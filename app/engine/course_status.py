"""Status computation for the "🎓 Python Learning" course -- shared by both
UIs (like app.engine.hub_status.compute_hub_status()) so the course
dashboard's chapter grid and XP tile are computed once, not duplicated
per-UI.

Chapters are never locked (every chapter is always browsable). A chapter
can hold one or several independent sub-topics (Lesson.topic, e.g. a
"Data Structures" chapter's Lists/Tuples/Dictionaries/Sets, or a
"Variables" chapter's Variables/Numbers/Strings/Booleans/Type Conversion)
-- topics within a chapter are never locked relative to each other either,
only the 3 items *within one topic* gate in order, via
is_topic_item_unlocked() below (a topic-scoped equivalent of
LessonEngine.is_unlocked(), which gates across a *whole* category and so
can't be reused directly once a category holds more than one topic)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Optional

from app.engine.categories import COURSE_CATEGORIES
from app.engine.lesson import Lesson
from app.engine.lesson_engine import LessonEngine
from app.progress.store import ProgressStore

COURSE_BADGE_ID = "course_graduate"
"""Awarded once every lesson across every COURSE_CATEGORIES chapter is
complete -- see maybe_award_course_badge()."""


@dataclass(frozen=True)
class TopicStatus:
    topic: str
    """"" for a chapter with no sub-grouping (every lesson in the category
    shares topic="") -- UI screens skip rendering a group heading in that
    case, so a single-topic chapter looks identical to before topics
    existed."""
    items: list[Lesson]
    completed_count: int
    total_count: int


@dataclass(frozen=True)
class ChapterStatus:
    category: str
    topics: list[TopicStatus]
    completed_count: int
    total_count: int


@dataclass(frozen=True)
class CourseStatus:
    chapters: list[ChapterStatus]
    items_done: int
    items_total: int
    stars_earned: int
    """Sum of reward_stars earned across this course's lessons specifically
    -- the course dashboard's "XP" tile. Not the app's global player XP."""


def _group_by_topic(items: list[Lesson], completed_ids: set[str]) -> list[TopicStatus]:
    """Groups `items` (already sorted by category_level) into TopicStatus
    entries, one per distinct Lesson.topic value, in order of first
    appearance -- so a chapter's topics render in the same order their
    lessons were authored in, not alphabetically."""
    order: list[str] = []
    grouped: dict[str, list[Lesson]] = {}
    for lesson in items:
        if lesson.topic not in grouped:
            grouped[lesson.topic] = []
            order.append(lesson.topic)
        grouped[lesson.topic].append(lesson)
    return [
        TopicStatus(
            topic=topic, items=grouped[topic],
            completed_count=sum(1 for lesson in grouped[topic] if lesson.id in completed_ids),
            total_count=len(grouped[topic]),
        )
        for topic in order
    ]


def compute_course_status(engine: LessonEngine, progress: ProgressStore) -> CourseStatus:
    completed_ids = set(progress.get_completed_lesson_ids())
    stars_by_lesson = progress.get_stars_by_lesson()

    chapters: list[ChapterStatus] = []
    items_done = 0
    items_total = 0
    stars_earned = 0
    for category in COURSE_CATEGORIES:
        items = engine.lessons_in_category(category)
        topics = _group_by_topic(items, completed_ids)
        completed_count = sum(topic.completed_count for topic in topics)
        total_count = sum(topic.total_count for topic in topics)
        chapters.append(ChapterStatus(
            category=category, topics=topics,
            completed_count=completed_count, total_count=total_count,
        ))
        items_done += completed_count
        items_total += total_count
        stars_earned += sum(stars_by_lesson.get(lesson.id, 0) for lesson in items)

    return CourseStatus(
        chapters=chapters, items_done=items_done, items_total=items_total,
        stars_earned=stars_earned,
    )


def is_topic_item_unlocked(lesson: Lesson, topic_items: list[Lesson], completed_ids: Collection[str]) -> bool:
    """Whether `lesson` is playable yet, scoped to just its own topic group
    (`topic_items` -- e.g. TopicStatus.items) rather than the whole
    category: the first item in a topic is always unlocked, and every
    later one needs every earlier item in that SAME topic done -- items in
    a sibling topic (e.g. Tuples) never block this one (e.g. Sets)."""
    ordered = sorted(topic_items, key=lambda item: item.category_level)
    index = ordered.index(lesson)
    if index == 0:
        return True
    completed = set(completed_ids)
    return all(other.id in completed for other in ordered[:index])


def next_topic_item(engine: LessonEngine, lesson: Lesson, completed_ids: Collection[str]) -> Optional[Lesson]:
    """The next not-yet-completed, unlocked item in the same topic group as
    `lesson` -- the topic-scoped equivalent of
    LessonEngine.next_unlocked_in_category(), needed for the lesson
    screen's "Next Lesson" button once a category holds more than one
    topic (that whole-category method would otherwise require every
    earlier topic's items done too, contradicting "topics are
    independent")."""
    peers = [item for item in engine.lessons_in_category(lesson.category) if item.topic == lesson.topic]
    peers.sort(key=lambda item: item.category_level)
    completed = set(completed_ids)
    for peer in peers:
        if peer.id not in completed and is_topic_item_unlocked(peer, peers, completed):
            return peer
    return None


def maybe_award_course_badge(engine: LessonEngine, progress: ProgressStore) -> None:
    """Awards COURSE_BADGE_ID once every lesson in every course chapter is
    complete. Safe to call after every course-lesson completion -- award_
    badge() is itself idempotent (INSERT OR IGNORE)."""
    completed_ids = set(progress.get_completed_lesson_ids())
    all_course_lesson_ids = [
        lesson.id for category in COURSE_CATEGORIES for lesson in engine.lessons_in_category(category)
    ]
    if all_course_lesson_ids and all(lesson_id in completed_ids for lesson_id in all_course_lesson_ids):
        progress.award_badge(COURSE_BADGE_ID)
