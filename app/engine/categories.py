"""Display metadata (title, icon) for lesson categories, used by the category browser.

Purely presentational -- adding a category here isn't required for the
engine to work (LessonEngine.categories() derives the actual set from
content), but a category without an entry here falls back to a generic
label in the UI.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryMeta:
    title: str
    icon: str


CATEGORY_META: dict[str, CategoryMeta] = {
    "basics": CategoryMeta("Python Basics", "🐍"),
    "numbers": CategoryMeta("Numbers", "🔢"),
    "addition": CategoryMeta("Addition", "➕"),
    "subtraction": CategoryMeta("Subtraction", "➖"),
    "multiplication": CategoryMeta("Multiplication", "✖️"),
    "division": CategoryMeta("Division", "➗"),
    "variables": CategoryMeta("Variables", "📦"),
    "strings": CategoryMeta("Strings", "🔤"),
    "input": CategoryMeta("Ask a Question", "🙋"),
    "conditionals": CategoryMeta("Decisions", "🚦"),
    "loops": CategoryMeta("Loops", "🔁"),
    "functions": CategoryMeta("Functions", "⚙️"),
    "lists": CategoryMeta("Lists", "🎒"),
    "games": CategoryMeta("Mini Games", "🎮"),
    "snake": CategoryMeta("Snake Project", "🐍"),
}

DEFAULT_META = CategoryMeta("More Adventures", "⭐")


def get_category_meta(category: str) -> CategoryMeta:
    return CATEGORY_META.get(category, DEFAULT_META)
