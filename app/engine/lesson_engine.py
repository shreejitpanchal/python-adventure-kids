"""Loads lesson content from YAML files, kept separate from application code.

Adding a lesson means adding a file under content/lessons/ — no code changes here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Collection, Optional

import yaml

from app.engine.lesson import Lesson

DEFAULT_CONTENT_DIR = Path(__file__).resolve().parent.parent.parent / "content" / "lessons"

TODAYS_MISSION_INTRO_CATEGORY = "basics"
TODAYS_MISSION_CATEGORIES = [
    "numbers", "addition", "subtraction", "multiplication", "division",
    "variables", "strings", "input", "conditionals", "loops", "functions", "lists",
]
"""The categories "Today's Mission" cycles through, in order, after the
one-time basics intro -- level 1 of every category here, then level 2 of
every category, and so on. Games, Snake, and every other bonus category
stay reachable through the category browser but are never auto-assigned."""


class LessonEngine:
    def __init__(self, content_dir: Path = DEFAULT_CONTENT_DIR):
        self.content_dir = content_dir
        self._lessons: dict[str, Lesson] = {}
        self._order: list[str] = []
        self._load()

    def _load(self) -> None:
        lessons = []
        for path in sorted(self.content_dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            lessons.append(Lesson(**data))
        lessons.sort(key=lambda lesson: lesson.level)
        self._order = [lesson.id for lesson in lessons]
        self._lessons = {lesson.id: lesson for lesson in lessons}

    def __len__(self) -> int:
        return len(self._order)

    def get(self, lesson_id: str) -> Lesson:
        return self._lessons[lesson_id]

    def has(self, lesson_id: str) -> bool:
        return lesson_id in self._lessons

    def first(self) -> Lesson:
        return self._lessons[self._order[0]]

    def next_after(self, lesson_id: str) -> Optional[Lesson]:
        """The next lesson in "Today's Mission" after lesson_id, or None if
        lesson_id isn't part of that sequence or was its last step.

        Positional lookup into main_path_lessons() (the computed
        round-robin order) rather than a hand-authored next_lesson_id
        chain -- see that method.
        """
        sequence = self.main_path_lessons()
        ids = [lesson.id for lesson in sequence]
        try:
            index = ids.index(lesson_id)
        except ValueError:
            return None
        return sequence[index + 1] if index + 1 < len(sequence) else None

    def all_in_order(self) -> list[Lesson]:
        return [self._lessons[lesson_id] for lesson_id in self._order]

    def main_path_lessons(self) -> list[Lesson]:
        """Today's Mission: the basics intro lesson(s) once, then every
        category_level of TODAYS_MISSION_CATEGORIES in turn -- level 1 of
        every category, then level 2 of every category, and so on, up to
        however many levels each category actually has. Computed live from
        category/category_level rather than a stored chain, so the guided
        sequence and the category browser can never drift apart."""
        sequence = list(self.lessons_in_category(TODAYS_MISSION_INTRO_CATEGORY))
        by_category = [self.lessons_in_category(category) for category in TODAYS_MISSION_CATEGORIES]
        max_level = max((len(lessons) for lessons in by_category), default=0)
        for level_index in range(max_level):
            for lessons in by_category:
                if level_index < len(lessons):
                    sequence.append(lessons[level_index])
        return sequence

    def resolve_current(
        self, completed_ids: Collection[str], stored_current_id: Optional[str] = None
    ) -> Lesson:
        """The lesson a child should land on next for "Today's Mission".

        Trusts a stored pointer only if it's still valid and not already
        completed; otherwise falls back to the first incomplete lesson in
        main_path_lessons(), or the last one if everything is done. This
        keeps old progress data working even after lessons are added,
        removed, or reordered. Categories outside TODAYS_MISSION_CATEGORIES
        (games, Snake, Code Crackers, ...) are never chosen here -- they're
        reached through the category browser instead.
        """
        completed = set(completed_ids)
        if stored_current_id and self.has(stored_current_id) and stored_current_id not in completed:
            return self.get(stored_current_id)
        main_path = self.main_path_lessons()
        for lesson in main_path:
            if lesson.id not in completed:
                return lesson
        return main_path[-1]

    # -- categories ---------------------------------------------------------
    def categories(self) -> list[str]:
        """Category slugs in curriculum order (by each category's first appearance)."""
        seen: list[str] = []
        for lesson in self.all_in_order():
            if lesson.category not in seen:
                seen.append(lesson.category)
        return seen

    def lessons_in_category(self, category: str) -> list[Lesson]:
        lessons = [lesson for lesson in self.all_in_order() if lesson.category == category]
        lessons.sort(key=lambda lesson: lesson.category_level)
        return lessons

    def is_unlocked(self, lesson: Lesson, completed_ids: Collection[str]) -> bool:
        """A level is unlocked once every earlier level in its category is complete."""
        if lesson.category_level <= 1:
            return True
        completed = set(completed_ids)
        earlier = [
            other for other in self.lessons_in_category(lesson.category)
            if other.category_level < lesson.category_level
        ]
        return all(other.id in completed for other in earlier)

    def next_unlocked_in_category(self, category: str, completed_ids: Collection[str]) -> Optional[Lesson]:
        """The first not-yet-completed, unlocked lesson in a category, for a
        "Play" button that jumps straight to where the child left off."""
        completed = set(completed_ids)
        for lesson in self.lessons_in_category(category):
            if lesson.id not in completed and self.is_unlocked(lesson, completed):
                return lesson
        return None

    def recommend_practice(self, lesson_id: str, completed_ids: Collection[str], limit: int = 3) -> list[Lesson]:
        """Up to `limit` lessons sharing a concept_tags entry with
        `lesson_id`, for the "Practice Quest" suggestion after repeated
        failures (app/progress/store.py's get_recent_failure_count()).
        Excludes the struggling lesson itself; a no-op (empty list) if it
        has no concept_tags to match against. See
        recommend_practice_for_tags() for the quiz-results equivalent,
        which starts from a raw tag set instead of one lesson."""
        tags = set(self.get(lesson_id).concept_tags) if self.has(lesson_id) else set()
        if not tags:
            return []
        return [
            lesson for lesson in self.recommend_practice_for_tags(tags, completed_ids, limit + 1)
            if lesson.id != lesson_id
        ][:limit]

    def recommend_practice_for_tags(
        self, tags: Collection[str], completed_ids: Collection[str], limit: int = 3,
    ) -> list[Lesson]:
        """Up to `limit` lessons sharing at least one of `tags` --
        the quiz results screen's "practice these next" recommendation,
        built from the union of concept_tags across every question the
        child got wrong this session. Prefers not-yet-completed lessons
        (no point suggesting something already mastered)."""
        tags = set(tags)
        if not tags:
            return []
        completed = set(completed_ids)
        candidates = [lesson for lesson in self.all_in_order() if set(lesson.concept_tags) & tags]
        candidates.sort(key=lambda lesson: lesson.id in completed)  # not-yet-completed first
        return candidates[:limit]

    def category_completion(self, completed_ids: Collection[str]) -> dict[str, tuple[int, int]]:
        """category -> (completed_count, total_count), in categories()
        order -- the shared "mastery per category" calculation for the
        parent dashboard, so CTk and Flet don't each reimplement it."""
        completed = set(completed_ids)
        result: dict[str, tuple[int, int]] = {}
        for category in self.categories():
            lessons = self.lessons_in_category(category)
            done = sum(1 for lesson in lessons if lesson.id in completed)
            result[category] = (done, len(lessons))
        return result
