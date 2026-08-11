"""Loads lesson content from YAML files, kept separate from application code.

Adding a lesson means adding a file under content/lessons/ — no code changes here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Collection, Optional

import yaml

from app.engine.lesson import Lesson

DEFAULT_CONTENT_DIR = Path(__file__).resolve().parent.parent.parent / "content" / "lessons"


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
        """The next lesson in the guided main-path chain, or None at the end.

        Follows next_lesson_id only -- no order-based fallback -- so bonus
        category levels (main_path=False) never leak into the guided
        "Today's Mission" flow just because they happen to sort after the
        last main-path lesson.
        """
        lesson = self.get(lesson_id)
        if lesson.next_lesson_id:
            return self._lessons.get(lesson.next_lesson_id)
        return None

    def all_in_order(self) -> list[Lesson]:
        return [self._lessons[lesson_id] for lesson_id in self._order]

    def main_path_lessons(self) -> list[Lesson]:
        return [lesson for lesson in self.all_in_order() if lesson.main_path]

    def resolve_current(
        self, completed_ids: Collection[str], stored_current_id: Optional[str] = None
    ) -> Lesson:
        """The lesson a child should land on next for "Today's Mission".

        Trusts a stored pointer only if it's still valid and not already
        completed; otherwise falls back to the first incomplete main-path
        lesson, or the last main-path lesson if everything is done. This
        keeps old progress data working even after lessons are added,
        removed, or reordered. Bonus category levels are never chosen here
        -- they're reached through the category browser instead.
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
