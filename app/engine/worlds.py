"""Worlds: named regions of the Adventure Map that group lesson categories
(Number Kingdom, Word Valley, ...). Like categories.py, this is a
presentational grouping over content -- a category missing from every
world still works, it just shows under the Uncharted Lands fallback -- but
completing a whole world is also a real achievement: a world badge (see
badges.py, world_badge_id()) and a "World complete!" ceremony on the
lesson screen.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Optional


@dataclass(frozen=True)
class World:
    id: str
    title: str
    icon: str
    color: str
    categories: tuple[str, ...]


WORLDS: list[World] = [
    World("number_kingdom", "Number Kingdom", "🏰", "#FF9F1C",
          ("numbers", "addition", "subtraction", "multiplication", "division")),
    World("word_valley", "Word Valley", "📜", "#EC407A",
          ("basics", "variables", "strings", "input")),
    World("logic_peaks", "Logic Peaks", "⛰️", "#7E57C2",
          ("conditionals", "loops", "functions", "lists")),
    World("arcade_islands", "Arcade Islands", "🏝️", "#26C6DA",
          ("games", "snake", "creative_arts", "rpg_quests", "arcade_lab", "robot_adventure")),
    World("bug_swamp", "Bug Swamp", "🐸", "#8D6E63",
          ("code_crackers", "advanced_code_crackers")),
    World("scholar_tower", "Scholar's Tower", "🗼", "#4F46E5",
          ("course_intro_setup", "course_variables", "course_data_structures", "course_advanced_concepts",
           "course_stdlib", "course_concurrency", "course_capstone")),
    World("ai_observatory", "AI Observatory", "🔭", "#7C4DFF",
          ("ai_foundations", "ai_tools", "ai_advanced")),
]

UNCHARTED = World("uncharted", "Uncharted Lands", "🧭", "#78909C", ())

_WORLD_BY_CATEGORY: dict[str, World] = {
    category: world for world in WORLDS for category in world.categories
}


def world_for_category(category: str) -> World:
    return _WORLD_BY_CATEGORY.get(category, UNCHARTED)


def world_badge_id(world: World) -> str:
    return f"world_{world.id}"


def worlds_in_order(categories: list[str]) -> list[tuple[World, list[str]]]:
    """Groups `categories` (in the order given, e.g. LessonEngine.categories())
    by world, ordering worlds by where each first appears in that list --
    so the map's first region is wherever the curriculum starts, not a
    fixed WORLDS order -- and keeping each world's categories in their
    given order. Worlds with no category present are omitted."""
    grouped: dict[str, list[str]] = {}
    order: list[World] = []
    for category in categories:
        world = world_for_category(category)
        if world.id not in grouped:
            grouped[world.id] = []
            order.append(world)
        grouped[world.id].append(category)
    return [(world, grouped[world.id]) for world in order]


@dataclass(frozen=True)
class WorldStatus:
    world: World
    done: int
    total: int

    @property
    def complete(self) -> bool:
        return self.total > 0 and self.done == self.total


def world_status(engine, world: World, completed_ids: Collection[str], categories: Optional[list[str]] = None) -> WorldStatus:
    """Lesson completion across the world's categories that exist in
    `engine` (or just `categories`, when a filtered map shows a subset)."""
    completed = set(completed_ids)
    done = 0
    total = 0
    for category in (categories if categories is not None else world.categories):
        for lesson in engine.lessons_in_category(category):
            total += 1
            if lesson.id in completed:
                done += 1
    return WorldStatus(world=world, done=done, total=total)


def newly_completed_world(
    engine, category: str, completed_before: Collection[str], completed_after: Collection[str],
) -> Optional[World]:
    """The world `category` belongs to, if it just became complete -- i.e.
    it is complete with `completed_after` and wasn't with `completed_before`.
    None for the Uncharted fallback (no ceremony for an unmapped category)."""
    world = world_for_category(category)
    if world is UNCHARTED:
        return None
    if not world_status(engine, world, completed_after).complete:
        return None
    if world_status(engine, world, completed_before).complete:
        return None
    return world
