"""Skill-based stars and the session combo -- pure rules, no UI.

Stars used to be a fixed per-lesson reward_stars. Now reward_stars is the
*maximum*, and an attempt earns fewer when the child leaned on hints or
needed several tries, so replaying a level to earn the missing star is a
real goal (ProgressStore.complete_lesson keeps the best star count).

The combo is a per-session count of lessons passed in a row without a
failed attempt in between (AppState.combo). From COMBO_THRESHOLD on, XP
for a first-time completion is multiplied -- a hot streak within one
sitting, distinct from the day streak.
"""
from __future__ import annotations

from typing import Optional

COMBO_THRESHOLD = 3
COMBO_XP_MULTIPLIER = 2
FAILURES_FOR_PENALTY = 2


def stars_for_attempt(max_stars: int, *, hints_used: int, failed_attempts: int) -> int:
    """max_stars, minus one for using any hint, minus one for
    FAILURES_FOR_PENALTY or more failed attempts -- never below 1, so a
    finished lesson always counts."""
    penalties = (1 if hints_used > 0 else 0) + (1 if failed_attempts >= FAILURES_FOR_PENALTY else 0)
    return max(1, max_stars - penalties)


def improvement_hint(earned: int, max_stars: int, *, hints_used: int, failed_attempts: int) -> Optional[str]:
    """One encouraging line on how to earn the missing star(s) -- None when
    the attempt already earned the maximum."""
    if earned >= max_stars:
        return None
    if hints_used > 0 and failed_attempts >= FAILURES_FOR_PENALTY:
        return "Replay with no hints and nail it first try for " + "⭐" * max_stars + "!"
    if hints_used > 0:
        return "Replay without hints for " + "⭐" * max_stars + "!"
    return "Replay and get it in fewer tries for " + "⭐" * max_stars + "!"


def combo_multiplier(combo: int) -> int:
    return COMBO_XP_MULTIPLIER if combo >= COMBO_THRESHOLD else 1


def combo_label(combo: int) -> Optional[str]:
    """Text for the combo chip, or None when there's nothing to show yet
    (a combo of 1 is just 'a lesson')."""
    if combo < 2:
        return None
    if combo_multiplier(combo) > 1:
        return f"Combo x{combo} — {COMBO_XP_MULTIPLIER}× XP!"
    return f"Combo x{combo} — one more for {COMBO_XP_MULTIPLIER}× XP"
