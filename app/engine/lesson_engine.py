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
        lesson = self.get(lesson_id)
        if lesson.next_lesson_id:
            return self._lessons.get(lesson.next_lesson_id)
        idx = self._order.index(lesson_id)
        if idx + 1 < len(self._order):
            return self._lessons[self._order[idx + 1]]
        return None

    def all_in_order(self) -> list[Lesson]:
        return [self._lessons[lesson_id] for lesson_id in self._order]

    def resolve_current(
        self, completed_ids: Collection[str], stored_current_id: Optional[str] = None
    ) -> Lesson:
        """The lesson a child should land on next.

        Trusts a stored pointer only if it's still valid and not already
        completed; otherwise falls back to the first incomplete lesson, or
        the last lesson if everything is done. This keeps old progress data
        working even after lessons are added, removed, or reordered.
        """
        completed = set(completed_ids)
        if stored_current_id and self.has(stored_current_id) and stored_current_id not in completed:
            return self.get(stored_current_id)
        for lesson in self.all_in_order():
            if lesson.id not in completed:
                return lesson
        return self.all_in_order()[-1]
