"""Pure status computation for the Learning Hub's 4 cards -- shared by both
UIs (like LessonEngine.category_completion()) so the "what should each card
say" logic exists exactly once, not duplicated per-UI.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.engine.categories import PROJECT_CATEGORIES, get_category_meta
from app.engine.lesson_engine import LessonEngine
from app.progress.store import ProgressStore

# Route-key -> a short, friendly label for the "Continue where you left off"
# resume banner. Keys match Settings.last_learning_route's semantic values --
# each UI's Hub screen maps the same key to its own concrete navigation call.
_ROUTE_LABELS: dict[str, str] = {
    "guided": "Today's Mission",
    "code_crackers": "Code Cracker Puzzles",
    "advanced_code_crackers": "Advanced Code Crackers",
    "projects": "Build a Project",
}


@dataclass(frozen=True)
class HubStatus:
    guided_status: str
    cracker_status: str
    advanced_cracker_status: str
    project_status: str
    resume_label: Optional[str]


def _category_progress(engine: LessonEngine, completed_ids, categories: list[str]) -> tuple[int, int]:
    completion = engine.category_completion(completed_ids)
    done = sum(completion[category][0] for category in categories if category in completion)
    total = sum(completion[category][1] for category in categories if category in completion)
    return done, total


def compute_hub_status(engine: LessonEngine, progress: ProgressStore, settings) -> HubStatus:
    completed_ids = progress.get_completed_lesson_ids()
    summary = progress.get_summary()

    current_lesson = engine.resolve_current(completed_ids, summary.current_lesson_id)
    category_title = get_category_meta(current_lesson.category).title
    guided_status = f"Next: {category_title} — Level {current_lesson.category_level}"

    cracker_done, cracker_total = _category_progress(engine, completed_ids, ["code_crackers"])
    cracker_status = f"{cracker_done}/{cracker_total} solved"

    advanced_done, advanced_total = _category_progress(engine, completed_ids, ["advanced_code_crackers"])
    advanced_cracker_status = f"{advanced_done}/{advanced_total} solved"

    project_status = f"{len(PROJECT_CATEGORIES)} categories available"

    route_key = getattr(settings, "last_learning_route", "")
    resume_label = f"Continue where you left off: {_ROUTE_LABELS[route_key]}" if route_key in _ROUTE_LABELS else None

    return HubStatus(
        guided_status=guided_status,
        cracker_status=cracker_status,
        advanced_cracker_status=advanced_cracker_status,
        project_status=project_status,
        resume_label=resume_label,
    )
