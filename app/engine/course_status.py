"""Status computation for the "🎓 Python Learning" course -- shared by both
UIs (like app.engine.hub_status.compute_hub_status()) so the course
dashboard's chapter grid and XP tile are computed once, not duplicated
per-UI.

Chapters are never locked (every chapter is always browsable); only the 3
items *within* a chapter gate in order, via the existing
LessonEngine.is_unlocked() -- there is no separate chapter-level unlock
concept here.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.engine.categories import COURSE_CATEGORIES
from app.engine.lesson import Lesson
from app.engine.lesson_engine import LessonEngine
from app.progress.store import ProgressStore

COURSE_BADGE_ID = "course_graduate"
"""Awarded once every lesson across every COURSE_CATEGORIES chapter is
complete -- see maybe_award_course_badge()."""


@dataclass(frozen=True)
class ChapterStatus:
    category: str
    items: list[Lesson]
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


def compute_course_status(engine: LessonEngine, progress: ProgressStore) -> CourseStatus:
    completed_ids = set(progress.get_completed_lesson_ids())
    stars_by_lesson = progress.get_stars_by_lesson()

    chapters: list[ChapterStatus] = []
    items_done = 0
    items_total = 0
    stars_earned = 0
    for category in COURSE_CATEGORIES:
        items = engine.lessons_in_category(category)
        completed_count = sum(1 for lesson in items if lesson.id in completed_ids)
        chapters.append(ChapterStatus(
            category=category, items=items,
            completed_count=completed_count, total_count=len(items),
        ))
        items_done += completed_count
        items_total += len(items)
        stars_earned += sum(stars_by_lesson.get(lesson.id, 0) for lesson in items)

    return CourseStatus(
        chapters=chapters, items_done=items_done, items_total=items_total,
        stars_earned=stars_earned,
    )


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
