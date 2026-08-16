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
    # -- Python Journey module badges (app/engine/learning_path.py) --------
    "module_python_starter": BadgeMeta(
        "Python Starter", "🚀", "Completed the Python Starter module!",
    ),
    "module_variables_and_input": BadgeMeta(
        "Variables and Input", "📦", "Completed the Variables and Input module!",
    ),
    "module_decisions": BadgeMeta(
        "Decisions", "🚦", "Completed the Decisions module!",
    ),
    "module_loops": BadgeMeta(
        "Loops", "🔁", "Completed the Loops module!",
    ),
    "module_functions": BadgeMeta(
        "Functions", "⚙️", "Completed the Functions module!",
    ),
    "module_collections": BadgeMeta(
        "Collections", "🎒", "Completed the Collections module!",
    ),
    "module_problem_solving": BadgeMeta(
        "Problem Solving", "🧩", "Completed the Problem Solving module!",
    ),
    "module_python_creator": BadgeMeta(
        "Python Creator", "🏆", "Completed the Python Creator module!",
    ),
    "python_journey_complete": BadgeMeta(
        "Python Journey Complete", "🌟", "Finished all 8 modules of the Python Journey!",
    ),
}

DEFAULT_BADGE_META = BadgeMeta("Mystery Badge", "🏅", "A special achievement!")


def get_badge_meta(badge_id: str) -> BadgeMeta:
    return BADGE_META.get(badge_id, DEFAULT_BADGE_META)
