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
    "course_graduate": BadgeMeta(
        "Python Learning Graduate", "🎓", "Completed every chapter of the Python Learning course!",
    ),
    "ai_ml_graduate": BadgeMeta(
        "AI & ML Explorer", "🤖", "Completed every chapter of the AI & Machine Learning course!",
    ),
    # One per World in app/engine/worlds.py (ids via world_badge_id()),
    # awarded by the lesson screen when the last level in a world is done.
    "world_number_kingdom": BadgeMeta(
        "Number Kingdom Champion", "🏰", "Finished every level in the Number Kingdom!",
    ),
    "world_word_valley": BadgeMeta(
        "Word Valley Wanderer", "📜", "Finished every level in Word Valley!",
    ),
    "world_logic_peaks": BadgeMeta(
        "Logic Peaks Climber", "⛰️", "Finished every level in the Logic Peaks!",
    ),
    "world_arcade_islands": BadgeMeta(
        "Arcade Islands Legend", "🏝️", "Built every game and artwork on the Arcade Islands!",
    ),
    "world_bug_swamp": BadgeMeta(
        "Bug Swamp Survivor", "🐸", "Squashed every bug in the Bug Swamp!",
    ),
    "world_scholar_tower": BadgeMeta(
        "Scholar's Tower Sage", "🗼", "Climbed every floor of the Scholar's Tower!",
    ),
    "world_ai_observatory": BadgeMeta(
        "AI Observatory Astronomer", "🔭", "Explored every corner of the AI Observatory!",
    ),
}

DEFAULT_BADGE_META = BadgeMeta("Mystery Badge", "🏅", "A special achievement!")


def get_badge_meta(badge_id: str) -> BadgeMeta:
    return BADGE_META.get(badge_id, DEFAULT_BADGE_META)
