from app.ui import theme_flet

_LOCKED_SKIN_KEYS = {"space_odyssey", "cyberpunk", "enchanted_forest"}
_ORIGINAL_SKIN_KEYS = {
    "sunny_light", "ocean_breeze", "sunset_glow", "forest_adventure", "midnight_dark", "galaxy",
}


def test_every_preset_key_matches_its_dict_key():
    for key, preset in theme_flet.THEME_PRESETS.items():
        assert preset.key == key


def test_original_six_presets_are_always_unlocked():
    for key in _ORIGINAL_SKIN_KEYS:
        assert theme_flet.THEME_PRESETS[key].min_level == 1


def test_new_adventure_skins_are_locked_behind_a_player_level():
    for key in _LOCKED_SKIN_KEYS:
        assert theme_flet.THEME_PRESETS[key].min_level > 1


def test_locked_skins_unlock_in_increasing_order():
    levels = [theme_flet.THEME_PRESETS[key].min_level for key in ("space_odyssey", "cyberpunk", "enchanted_forest")]
    assert levels == sorted(levels)
    assert len(set(levels)) == len(levels)


def test_every_preset_key_set_matches_original_plus_locked():
    assert set(theme_flet.THEME_PRESETS.keys()) == _ORIGINAL_SKIN_KEYS | _LOCKED_SKIN_KEYS


def test_every_preset_color_is_valid_hex():
    color_fields = (
        "bg", "card", "text", "text_muted", "primary", "primary_hover",
        "success", "success_hover", "warning", "danger", "star",
    )
    for preset in theme_flet.THEME_PRESETS.values():
        for field_name in color_fields:
            value = getattr(preset, field_name)
            assert value.startswith("#") and len(value) == 7
            int(value[1:], 16)


def test_get_preset_falls_back_to_default_for_unknown_key():
    preset = theme_flet.get_preset("not_a_real_key")
    assert preset.key == theme_flet.DEFAULT_THEME_KEY


# -- font family + size -------------------------------------------------------
def test_resolve_font_family_known_keys():
    assert theme_flet.resolve_font_family("default") == "Baloo 2"
    assert theme_flet.resolve_font_family("classic") == "Roboto"


def test_resolve_font_family_falls_back_to_default_for_unknown_key():
    assert theme_flet.resolve_font_family("not_a_real_key") == theme_flet.FONT_FAMILY_PRESETS[
        theme_flet.DEFAULT_FONT_FAMILY_KEY
    ]


def test_resolve_font_scale_known_keys():
    assert theme_flet.resolve_font_scale("small") == 0.85
    assert theme_flet.resolve_font_scale("medium") == 1.0
    assert theme_flet.resolve_font_scale("large") == 1.2
    assert theme_flet.resolve_font_scale("extra_large") == 1.4


def test_resolve_font_scale_falls_back_to_default_for_unknown_key():
    assert theme_flet.resolve_font_scale("not_a_real_key") == 1.0


def test_scaled_multiplies_and_rounds():
    assert theme_flet.scaled(15, 1.4) == round(15 * 1.4)
    assert theme_flet.scaled(20, 0.85) == round(20 * 0.85)


def test_scaled_never_rounds_down_to_zero():
    assert theme_flet.scaled(1, 0.1) >= 1
