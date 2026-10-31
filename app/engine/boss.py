"""World boss battles: a short quiz drawn from everything a World teaches,
unlocked once every level in that World is complete, beaten at
BOSS_PASS_PERCENT, worth a boss badge (registered in badges.py). Pure
rules -- the quiz screen runs the fight, this module only says which
questions, when, and what counts as a win.
"""
from __future__ import annotations

from typing import Collection, Optional

from app.engine.worlds import WORLDS, World, world_status

BOSS_QUESTION_COUNT = 8
BOSS_PASS_PERCENT = 70


def boss_badge_id(world: World) -> str:
    return f"boss_{world.id}"


def world_by_id(world_id: str) -> Optional[World]:
    return next((world for world in WORLDS if world.id == world_id), None)


def boss_tags(engine, world: World) -> set[str]:
    """Every concept tag taught anywhere in the world -- the question pool
    filter (QuizEngine.start_session_for_tags falls back to the full bank
    if nothing matches, so a world with untagged lessons still has a
    boss)."""
    tags: set[str] = set()
    for category in world.categories:
        for lesson in engine.lessons_in_category(category):
            tags.update(lesson.concept_tags or [])
    return tags


def boss_unlocked(engine, world: World, completed_ids: Collection[str]) -> bool:
    return world_status(engine, world, completed_ids).complete


def boss_beaten(world: World, badge_ids: Collection[str]) -> bool:
    return boss_badge_id(world) in set(badge_ids)


def boss_won(score: int, total: int) -> bool:
    return total > 0 and round(100 * score / total) >= BOSS_PASS_PERCENT


def boss_title(world: World) -> str:
    return f"⚔️ Boss: {world.title}"


def boss_result_line(world: World, won: bool, score: int, total: int) -> str:
    if won:
        return f"You defeated the {world.title} boss! {score}/{total} — champion! 🏆"
    return f"The boss shrugged it off ({score}/{total}). Replay a level and come back stronger!"
