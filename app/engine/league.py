"""The weekly league: a small, fully offline leaderboard of Codey's friends
whose scores are generated around the child's own weekly XP, so the child
usually sits 2nd or 3rd and can overtake with one more lesson -- the
Duolingo-style nudge, without any network or real other players.

Pure rules: weekly_xp_from_events() tallies XP from the week's
activity_log events (ProgressStore.get_week_activity), league_standings()
builds the table deterministically from the ISO week key so it's stable
all week and changes only as the child's XP does. Settings.league_enabled
lets a parent switch the whole thing off.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

FRIENDS: list[tuple[str, str]] = [
    ("Ruby", "🦊"), ("Max", "🐼"), ("Zoe", "🐨"), ("Leo", "🦁"), ("Mia", "🐰"),
]
# Friend score as a share of the child's weekly XP (top to bottom): one
# friend just ahead, the rest behind -- so there is always someone to catch
# and always someone caught.
_FACTORS = (1.12, 0.85, 0.65, 0.45, 0.25)
_MIN_BASE_XP = 40
MEDALS = ("🥇", "🥈", "🥉")


@dataclass(frozen=True)
class Standing:
    name: str
    emoji: str
    xp: int
    is_child: bool


def _xp_from_detail(detail: str, key: str) -> int:
    if detail and detail.startswith(f"{key}="):
        try:
            return int(detail.split("=", 1)[1])
        except ValueError:
            return 0
    return 0


def weekly_xp_from_events(events: Iterable[tuple]) -> int:
    """Approximates the week's XP from the events already logged: a
    completed lesson is worth its stars x10, a quiz its score x5, and the
    chest/quest bonuses carry their XP in `detail`."""
    total = 0
    for _lesson_id, event_type, detail in events:
        if event_type == "lesson_completed":
            total += _xp_from_detail(detail, "stars") * 10
        elif event_type == "quiz_completed" and detail.startswith("score="):
            try:
                total += int(detail.split("=", 1)[1].split("/", 1)[0]) * 5
            except ValueError:
                pass
        elif event_type in ("chest_opened", "quest_bonus_claimed"):
            total += _xp_from_detail(detail, "xp")
    return total


def league_standings(child_name: str, child_xp: int, week_key: str) -> list[Standing]:
    """Everyone in the league, highest XP first; ties go to the child."""
    rng = random.Random(f"{week_key}:{child_xp // 50}")
    base = max(child_xp, _MIN_BASE_XP)
    standings = [Standing(child_name or "You", "🤖", child_xp, True)]
    for (name, emoji), factor in zip(FRIENDS, _FACTORS):
        # Floor at 5 so a brand-new child (0 XP) is always last -- and every
        # friend is catchable with a single lesson.
        xp = max(5, round((base * factor + rng.uniform(-8, 8)) / 5) * 5)
        standings.append(Standing(name, emoji, xp, False))
    standings.sort(key=lambda s: (-s.xp, 0 if s.is_child else 1))
    return standings


def child_rank(standings: list[Standing]) -> int:
    return next(i + 1 for i, s in enumerate(standings) if s.is_child)


def league_line(standings: list[Standing]) -> str:
    """Codey's nudge under the table."""
    rank = child_rank(standings)
    if rank == 1:
        return "You're leading the league this week! Keep it up 🥇"
    above = standings[rank - 2]
    child = standings[rank - 1]
    gap = above.xp - child.xp
    return f"{gap} XP behind {above.name} {above.emoji} — one lesson could do it!"
