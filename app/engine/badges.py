"""Display metadata (title, icon, description) for badges, used by the
Trophy Room -- mirrors app/engine/categories.py's CATEGORY_META pattern.

Purely presentational -- awarding a badge (app.progress.store.ProgressStore
.award_badge()) never needs an entry here; a badge without one just falls
back to a generic title/icon in the UI.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BadgeMeta:
    title: str
    icon: str
    description: str


BADGE_META: dict[str, BadgeMeta] = {
    "first_program": BadgeMeta(
        "First Program", "🥇", "Wrote and ran your very first Python program!",
    ),
    "math_master": BadgeMeta(
        "Math Master", "🧮", "Mastered addition, subtraction, multiplication, and division!",
    ),
    "python_explorer": BadgeMeta(
        "Python Explorer", "🧭", "Learned how to ask questions with input()!",
    ),
    "loop_wizard": BadgeMeta(
        "Loop Wizard", "🌀", "Mastered repeating code with loops!",
    ),
    "game_creator": BadgeMeta(
        "Game Creator", "🕹️", "Built mini-games using randomness!",
    ),
}

DEFAULT_BADGE_META = BadgeMeta("Mystery Badge", "🏅", "A special achievement!")


def get_badge_meta(badge_id: str) -> BadgeMeta:
    return BADGE_META.get(badge_id, DEFAULT_BADGE_META)
