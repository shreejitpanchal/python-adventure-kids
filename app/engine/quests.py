"""Daily quests: three small goals per (UTC) day, picked deterministically
from a pool so the board is the same all day, with progress derived from
the day's activity_log events -- no quest-progress table to keep in sync.
The only stored state is whether today's completion bonus has been
claimed (ProgressStore.claim_quest_bonus / profile.last_quest_bonus_date).

Events are (lesson_id, event_type, detail) triples as
ProgressStore.get_todays_activity() returns them. Event types are the ones
the UI already logs: lesson_completed (detail "stars=N"), hint_used,
chest_opened, quiz_completed.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, Optional

QUESTS_PER_DAY = 3
QUEST_BONUS_XP = 50

Event = tuple  # (lesson_id: Optional[str], event_type: str, detail: str)


@dataclass(frozen=True)
class QuestDef:
    id: str
    title: str
    icon: str
    target: int


QUEST_POOL: list[QuestDef] = [
    QuestDef("finish_lesson", "Finish a lesson", "📘", 1),
    QuestDef("finish_two", "Finish 2 lessons", "📚", 2),
    QuestDef("earn_stars", "Earn 5 stars", "⭐", 5),
    QuestDef("open_chest", "Open the Daily Treasure", "🎁", 1),
    QuestDef("play_quiz", "Play a quiz", "❓", 1),
    QuestDef("no_hints", "Pass a lesson without hints", "🧠", 1),
]


@dataclass(frozen=True)
class QuestStatus:
    quest: QuestDef
    progress: int

    @property
    def done(self) -> bool:
        return self.progress >= self.quest.target

    @property
    def shown_progress(self) -> int:
        return min(self.progress, self.quest.target)


def daily_quests(date_iso: str) -> list[QuestDef]:
    """The day's QUESTS_PER_DAY quests, in a stable order -- seeded by the
    date so every rebuild of the Hub shows the same board."""
    chooser = random.Random(date_iso)
    picked = chooser.sample(QUEST_POOL, QUESTS_PER_DAY)
    picked.sort(key=lambda quest: QUEST_POOL.index(quest))
    return picked


def _stars_from_detail(detail: Optional[str]) -> int:
    if detail and detail.startswith("stars="):
        try:
            return int(detail.split("=", 1)[1])
        except ValueError:
            return 0
    return 0


def quest_progress(quests: Iterable[QuestDef], events: Iterable[Event]) -> list[QuestStatus]:
    events = list(events)
    completed = [event for event in events if event[1] == "lesson_completed"]
    hinted_lessons = {event[0] for event in events if event[1] == "hint_used"}
    counts = {
        "finish_lesson": len(completed),
        "finish_two": len(completed),
        "earn_stars": sum(_stars_from_detail(event[2]) for event in completed),
        "open_chest": sum(1 for event in events if event[1] == "chest_opened"),
        "play_quiz": sum(1 for event in events if event[1] == "quiz_completed"),
        "no_hints": sum(1 for event in completed if event[0] not in hinted_lessons),
    }
    return [QuestStatus(quest=quest, progress=counts.get(quest.id, 0)) for quest in quests]


def all_quests_done(statuses: Iterable[QuestStatus]) -> bool:
    statuses = list(statuses)
    return bool(statuses) and all(status.done for status in statuses)
