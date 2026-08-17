"""Display metadata (title, icon, color) for lesson categories, used by the
category browser -- one distinct, solid color per topic, Scratch-style
(Motion=blue, Looks=purple, Events=gold, ...) so a child can recognize a
category by color alone, not just its label.

Purely presentational -- adding a category here isn't required for the
engine to work (LessonEngine.categories() derives the actual set from
content), but a category without an entry here falls back to a generic
label/color in the UI.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryMeta:
    title: str
    icon: str
    color: str


CATEGORY_META: dict[str, CategoryMeta] = {
    "basics": CategoryMeta("Python Basics", "🐍", "#4C97FF"),
    "numbers": CategoryMeta("Numbers", "🔢", "#FF9F1C"),
    "addition": CategoryMeta("Addition", "➕", "#4CAF50"),
    "subtraction": CategoryMeta("Subtraction", "➖", "#F06292"),
    "multiplication": CategoryMeta("Multiplication", "✖️", "#9C6ADE"),
    "division": CategoryMeta("Division", "➗", "#26C6DA"),
    "variables": CategoryMeta("Variables", "📦", "#FFCA28"),
    "strings": CategoryMeta("Strings", "🔤", "#EC407A"),
    "input": CategoryMeta("Ask a Question", "🙋", "#29B6F6"),
    "conditionals": CategoryMeta("Decisions", "🚦", "#FF7043"),
    "loops": CategoryMeta("Loops", "🔁", "#26A69A"),
    "functions": CategoryMeta("Functions", "⚙️", "#7E57C2"),
    "lists": CategoryMeta("Lists", "🎒", "#8D6E63"),
    "games": CategoryMeta("Mini Games", "🎮", "#EF5350"),
    "snake": CategoryMeta("Snake Project", "🐍", "#66BB6A"),
    "quiz": CategoryMeta("Quiz", "❓", "#5C6BC0"),
    "code_crackers": CategoryMeta("Code Crackers", "🧩", "#D4A017"),
    "creative_arts": CategoryMeta("Creative Arts", "🎨", "#FF6EC7"),
    "rpg_quests": CategoryMeta("RPG Quests", "⚔️", "#8B4513"),
    "arcade_lab": CategoryMeta("Arcade Lab", "🏓", "#00ACC1"),
    "robot_adventure": CategoryMeta("Robot Adventure", "🤖", "#546E7A"),
    "advanced_code_crackers": CategoryMeta("Advanced Code Crackers", "🕵️", "#37474F"),
}

DEFAULT_META = CategoryMeta("More Adventures", "⭐", "#78909C")


def get_category_meta(category: str) -> CategoryMeta:
    return CATEGORY_META.get(category, DEFAULT_META)


PROJECT_CATEGORIES = ["games", "snake", "creative_arts", "rpg_quests", "arcade_lab", "robot_adventure"]
"""The "Build a Project" grouping for the Learning Hub -- every category
that isn't a core skill-practice track (see LessonEngine.TODAYS_MISSION_
CATEGORIES), "basics", or one of the two Code Crackers tracks (which get
their own direct Hub cards instead of being lumped in here)."""
