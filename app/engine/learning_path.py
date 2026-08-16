"""Loads the Python Journey curriculum from YAML, kept separate from
application code -- see content/learning_path.yaml.

Mirrors LessonEngine's philosophy of computing status live rather than
storing it: module lock/available/in-progress/completed state, "Module X
of Y", and which module badges are newly earned are all derived from
completed_lesson_ids on every call, never persisted separately. That
makes migration free -- a returning child who already finished lessons
the old way sees correct module progress the very first time they open
Python Journey, with no migration script (see newly_earned_module_badges()
below for the one-time "catch up" award check that follows from this).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Collection, Literal, Optional

import yaml

DEFAULT_LEARNING_PATH_PATH = Path(__file__).resolve().parent.parent.parent / "content" / "learning_path.yaml"

ModuleStatus = Literal["locked", "available", "in_progress", "completed"]


@dataclass(frozen=True)
class Module:
    id: str
    title: str
    order: int
    icon: str
    description: str
    required_lesson_ids: list[str]
    checkpoint_lesson_id: Optional[str]
    badge_id: str


class LearningPathEngine:
    def __init__(self, path: Path = DEFAULT_LEARNING_PATH_PATH):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        modules = [
            Module(
                id=m["id"], title=m["title"], order=m["order"], icon=m["icon"],
                description=m.get("description", ""),
                required_lesson_ids=list(m.get("required_lesson_ids", [])),
                checkpoint_lesson_id=m.get("checkpoint_lesson_id"),
                badge_id=m["badge_id"],
            )
            for m in data["modules"]
        ]
        modules.sort(key=lambda module: module.order)
        self._modules = modules
        self._by_id = {module.id: module for module in modules}

    def modules(self) -> list[Module]:
        return list(self._modules)

    def get(self, module_id: str) -> Module:
        return self._by_id[module_id]

    def module_lesson_ids(self, module_id: str) -> list[str]:
        """Required lessons, in order, followed by the checkpoint (if set)."""
        module = self._by_id[module_id]
        ids = list(module.required_lesson_ids)
        if module.checkpoint_lesson_id:
            ids.append(module.checkpoint_lesson_id)
        return ids

    def is_module_complete(self, module_id: str, completed_ids: Collection[str]) -> bool:
        completed = set(completed_ids)
        return all(lesson_id in completed for lesson_id in self.module_lesson_ids(module_id))

    def module_status(self, module_id: str, completed_ids: Collection[str]) -> ModuleStatus:
        completed = set(completed_ids)
        if self.is_module_complete(module_id, completed):
            return "completed"

        index = self._modules.index(self._by_id[module_id])
        if index > 0 and not self.is_module_complete(self._modules[index - 1].id, completed):
            return "locked"

        if any(lesson_id in completed for lesson_id in self.module_lesson_ids(module_id)):
            return "in_progress"
        return "available"

    def is_lesson_unlocked(self, module_id: str, lesson_id: str, completed_ids: Collection[str]) -> bool:
        """A lesson within a module unlocks once its module is unlocked
        and every earlier lesson in that module's list (required lessons,
        then the checkpoint) is completed -- mirrors
        LessonEngine.is_unlocked()'s category_level logic, keyed by list
        position instead of an integer field."""
        ids = self.module_lesson_ids(module_id)
        if lesson_id not in ids:
            return False
        if self.module_status(module_id, completed_ids) == "locked":
            return False
        completed = set(completed_ids)
        position = ids.index(lesson_id)
        return all(earlier_id in completed for earlier_id in ids[:position])

    def current_module(self, completed_ids: Collection[str]) -> Module:
        """The first not-yet-completed module, or the last module if
        everything is done -- mirrors LessonEngine.resolve_current()'s
        fallback shape."""
        for module in self._modules:
            if not self.is_module_complete(module.id, completed_ids):
                return module
        return self._modules[-1]

    def progress_summary(self, completed_ids: Collection[str]) -> tuple[int, int]:
        """(modules_completed, total_modules) -- "Module X of Y" on the
        Journey map header."""
        completed = set(completed_ids)
        done = sum(1 for module in self._modules if self.is_module_complete(module.id, completed))
        return done, len(self._modules)

    def newly_earned_module_badges(
        self, completed_ids: Collection[str], already_awarded_badge_ids: Collection[str],
    ) -> list[str]:
        """Module badge ids satisfied by completed_ids but not yet in
        already_awarded_badge_ids. Called every time the Journey screen
        loads (award_badge() is idempotent, so re-checking is cheap and
        safe) -- this is the whole migration story: a child who finished
        a module's lessons before this feature existed gets the badge
        retroactively, with no separate one-time migration step."""
        completed = set(completed_ids)
        awarded = set(already_awarded_badge_ids)
        return [
            module.badge_id
            for module in self._modules
            if module.badge_id not in awarded and self.is_module_complete(module.id, completed)
        ]

    def all_modules_complete(self, completed_ids: Collection[str]) -> bool:
        completed = set(completed_ids)
        return all(self.is_module_complete(module.id, completed) for module in self._modules)
