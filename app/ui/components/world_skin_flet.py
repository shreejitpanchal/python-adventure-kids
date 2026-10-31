"""Per-World re-skins: entering a World's screens (its category levels and
its lessons) swaps the sky, page background, card color and primary accent
so Number Kingdom and Arcade Islands feel like different places, while the
child's chosen skin still decides light vs dark and the text/success/
warning palette.

skinned_theme() returns a *derived* ThemePreset (dataclasses.replace) whose
key is "<skin>+<world>"; its sky is registered with theme_flet.register_sky
so adventure_kit_flet.sky_gradient() picks it up without SKY_COLORS (the
per-skin table Settings enumerates) growing a row per world. Flet only.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass

from app.engine.worlds import World
from app.ui.color_utils import darken, lighten
from app.ui.theme_flet import ThemePreset, register_sky


@dataclass(frozen=True)
class WorldSkin:
    sky_top: str
    sky_bottom: str
    bg: str
    card: str
    primary: str


# Light-mode skins; dark-mode ones are derived (see _dark_variant) so every
# world works on all nine presets without a second hand-tuned table.
WORLD_SKINS: dict[str, WorldSkin] = {
    "number_kingdom": WorldSkin("#FFD79A", "#FFF4E0", "#FFF4E0", "#FFFDF7", "#FF9F1C"),
    "word_valley": WorldSkin("#FFC4DA", "#FFF0F5", "#FFF0F5", "#FFFBFD", "#EC407A"),
    "logic_peaks": WorldSkin("#D9CCF5", "#F3EFFC", "#F3EFFC", "#FCFAFF", "#7E57C2"),
    "arcade_islands": WorldSkin("#B2EEF5", "#EAFBFD", "#EAFBFD", "#F9FEFF", "#26C6DA"),
    "bug_swamp": WorldSkin("#D7C7BE", "#F4EFEB", "#F4EFEB", "#FDFBF9", "#8D6E63"),
    "scholar_tower": WorldSkin("#C9C5F5", "#EEEDFC", "#EEEDFC", "#FAFAFF", "#4F46E5"),
    "ai_observatory": WorldSkin("#D5C4FF", "#F1EBFF", "#F1EBFF", "#FBF9FF", "#7C4DFF"),
}


def _dark_variant(skin: WorldSkin, theme: ThemePreset) -> WorldSkin:
    """A dark preset keeps its own deep bg/card and only takes the world's
    hue into the sky band and the primary accent."""
    return WorldSkin(
        sky_top=darken(skin.primary, 0.55), sky_bottom=theme.bg,
        bg=theme.bg, card=theme.card, primary=lighten(skin.primary, 0.12),
    )


def world_skin(world: World, theme: ThemePreset) -> WorldSkin | None:
    base = WORLD_SKINS.get(world.id)
    if base is None:
        return None
    return _dark_variant(base, theme) if theme.is_dark else base


def skinned_theme(theme: ThemePreset, world: World) -> ThemePreset:
    """The preset re-colored for `world`; the preset itself for a world
    without a skin (Uncharted Lands)."""
    skin = world_skin(world, theme)
    if skin is None:
        return theme
    key = f"{theme.key}+{world.id}"
    register_sky(key, skin.sky_top, skin.sky_bottom)
    return dataclasses.replace(
        theme, key=key, bg=skin.bg, card=skin.card,
        primary=skin.primary, primary_hover=darken(skin.primary, 0.15),
    )


def skinned_key_parts(key: str) -> tuple[str, str | None]:
    """("forest_adventure", "logic_peaks") for a derived key, (key, None)
    for a plain preset key."""
    if "+" in key:
        base, world_id = key.split("+", 1)
        return base, world_id
    return key, None
