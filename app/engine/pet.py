"""Codey's buddy: a creature that hatches and grows with the player's total
XP. Pure rules -- the stage is *derived* from ProgressStore's total XP, so
there is no pet table to keep in sync and nothing to migrate; the UI
(app/ui/components/pet_flet.py) only draws whichever stage the XP says.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PetStage:
    id: str
    name: str
    min_xp: int
    emoji: str
    """Fallback face for text-only places (HUD chips, captions)."""
    description: str
    size: int
    """Drawn body size in px -- the buddy visibly grows."""


PET_STAGES: tuple[PetStage, ...] = (
    PetStage("egg", "Mystery Egg", 0, "🥚", "Something is wriggling inside. Earn XP to hatch it!", 44),
    PetStage("hatchling", "Hatchling", 50, "🐣", "It hatched! A tiny blob with big eyes.", 48),
    PetStage("sprout", "Sprout", 150, "🌱", "A leaf has grown on its head. It loves loops.", 54),
    PetStage("scamp", "Scamp", 350, "🐾", "Ears, a tail, and endless energy.", 60),
    PetStage("guardian", "Guardian", 700, "🛡️", "Wings! It watches over your streak.", 68),
    PetStage("legend", "Legend", 1200, "👑", "A crowned legend of the Adventure Map.", 76),
)


def pet_stage(total_xp: int) -> PetStage:
    """The highest stage whose threshold the XP has reached."""
    current = PET_STAGES[0]
    for stage in PET_STAGES:
        if total_xp >= stage.min_xp:
            current = stage
    return current


def next_pet_stage(total_xp: int) -> Optional[PetStage]:
    """The stage after the current one, or None at the top."""
    current = pet_stage(total_xp)
    for stage in PET_STAGES:
        if stage.min_xp > current.min_xp:
            return stage
    return None


def pet_progress(total_xp: int) -> tuple[int, int]:
    """(xp into the current stage, xp the stage spans) -- (0, 0) at the top
    so a power bar shows full."""
    current = pet_stage(total_xp)
    upcoming = next_pet_stage(total_xp)
    if upcoming is None:
        return 0, 0
    return total_xp - current.min_xp, upcoming.min_xp - current.min_xp


def pet_line(total_xp: int) -> str:
    """What the buddy card says under its name."""
    upcoming = next_pet_stage(total_xp)
    if upcoming is None:
        return "Fully grown — a true legend! 👑"
    into, span = pet_progress(total_xp)
    return f"{span - into} XP until it becomes a {upcoming.name}!"


def newly_reached_stage(xp_before: int, xp_after: int) -> Optional[PetStage]:
    """The stage crossed by an XP gain, if any -- for the reward moment."""
    before = pet_stage(xp_before)
    after = pet_stage(xp_after)
    return after if after.min_xp > before.min_xp else None
