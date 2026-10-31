"""world_skin_flet: a World re-colors the preset without touching its text
palette, registers its sky, and leaves unskinned worlds alone."""
from __future__ import annotations

from app.engine.worlds import UNCHARTED, WORLDS, world_for_category
from app.ui.components.adventure_kit_flet import sky_gradient
from app.ui.components.world_skin_flet import WORLD_SKINS, skinned_key_parts, skinned_theme, world_skin
from app.ui.theme_flet import THEME_PRESETS, get_preset, sky_colors


def test_every_world_has_a_skin_and_uncharted_lands_do_not():
    assert set(WORLD_SKINS) == {world.id for world in WORLDS}
    assert world_skin(UNCHARTED, get_preset("sunny_light")) is None


def test_skinned_theme_recolors_bg_card_and_primary_but_keeps_the_text_palette():
    base = get_preset("sunny_light")
    world = world_for_category("loops")
    skinned = skinned_theme(base, world)
    assert skinned.key == f"{base.key}+{world.id}"
    assert skinned.bg == WORLD_SKINS[world.id].bg and skinned.primary == WORLD_SKINS[world.id].primary
    assert (skinned.text, skinned.text_muted, skinned.success, skinned.warning, skinned.star) == (
        base.text, base.text_muted, base.success, base.warning, base.star,
    )
    assert skinned.is_dark is base.is_dark
    assert sky_colors(skinned) == (WORLD_SKINS[world.id].sky_top, WORLD_SKINS[world.id].sky_bottom)
    assert sky_gradient(skinned).colors == list(sky_colors(skinned))
    assert skinned_key_parts(skinned.key) == (base.key, world.id)
    assert skinned_key_parts(base.key) == (base.key, None)


def test_dark_presets_keep_their_deep_bg_and_only_take_the_hue():
    dark = get_preset("midnight_dark")
    world = world_for_category("numbers")
    skinned = skinned_theme(dark, world)
    assert skinned.bg == dark.bg and skinned.card == dark.card
    assert skinned.primary != dark.primary
    top, bottom = sky_colors(skinned)
    assert bottom == dark.bg
    assert top.startswith("#") and top != dark.bg, "a darkened World hue tops the sky"


def test_unskinned_world_returns_the_preset_itself():
    base = get_preset("galaxy")
    assert skinned_theme(base, UNCHARTED) is base


def test_every_preset_can_be_skinned_for_every_world():
    for preset in THEME_PRESETS.values():
        for world in WORLDS:
            skinned = skinned_theme(preset, world)
            assert skinned.key.startswith(preset.key + "+")
            assert all(color.startswith("#") for color in (skinned.bg, skinned.card, skinned.primary))
