"""Player-level titles and Codey's matching look -- purely presentational
metadata over ProgressStore.get_player_level(), in the same spirit as
categories.py / badges.py: the level math lives in the store, this only
names the tiers and picks the accessory Codey wears at each."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LevelTitle:
    min_level: int
    title: str
    codey_accessory: str
    """Emoji shown as a small badge on Codey's face disc; "" for none."""


LEVEL_TITLES: list[LevelTitle] = [
    LevelTitle(1, "Curious Coder", ""),
    LevelTitle(3, "Bug Hunter", "🧢"),
    LevelTitle(5, "Loop Wizard", "🧙"),
    LevelTitle(8, "Function Forger", "🦸"),
    LevelTitle(12, "Data Dragon Tamer", "🐉"),
    LevelTitle(16, "Python Master", "👑"),
]


def level_title(level: int) -> LevelTitle:
    current = LEVEL_TITLES[0]
    for tier in LEVEL_TITLES:
        if level >= tier.min_level:
            current = tier
    return current


def next_title_after(level: int) -> Optional[LevelTitle]:
    """The first tier above `level`, or None at the top."""
    for tier in LEVEL_TITLES:
        if tier.min_level > level:
            return tier
    return None
