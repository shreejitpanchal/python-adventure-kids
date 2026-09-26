"""Codey's closet: cosmetic outfits bought with stars -- the first thing
stars can be *spent* on (they're otherwise a score). Purely presentational
metadata in the categories.py/badges.py style; ownership and the star
balance live in ProgressStore (buy_outfit/equip_outfit/get_star_balance).

An equipped outfit replaces the level-title accessory on Codey's disc
(see codey_accessory()); taking it off shows the title accessory again.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.engine.titles import level_title


@dataclass(frozen=True)
class Outfit:
    id: str
    title: str
    emoji: str
    price: int
    """In stars."""


OUTFITS: list[Outfit] = [
    Outfit("glasses", "Smart Glasses", "👓", 10),
    Outfit("bow", "Bow", "🎀", 10),
    Outfit("headphones", "Headphones", "🎧", 20),
    Outfit("party_hat", "Party Hat", "🥳", 20),
    Outfit("top_hat", "Top Hat", "🎩", 30),
    Outfit("rainbow", "Rainbow", "🌈", 35),
    Outfit("unicorn", "Unicorn Horn", "🦄", 45),
    Outfit("rocket", "Rocket Pack", "🚀", 55),
    Outfit("crown", "Royal Crown", "👑", 80),
]

_BY_ID = {outfit.id: outfit for outfit in OUTFITS}


def get_outfit(outfit_id: str) -> Optional[Outfit]:
    return _BY_ID.get(outfit_id)


def codey_accessory(equipped_outfit_id: Optional[str], level: int) -> str:
    """What Codey wears: the equipped outfit's emoji, else the level
    title's accessory (an unknown/removed outfit id also falls back)."""
    outfit = get_outfit(equipped_outfit_id) if equipped_outfit_id else None
    if outfit is not None:
        return outfit.emoji
    return level_title(level).codey_accessory
