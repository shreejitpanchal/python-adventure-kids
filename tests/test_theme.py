import pytest

from app.ui import theme


@pytest.fixture(autouse=True)
def _restore_default_theme():
    """apply_theme() mutates module-level globals, so tests must not leak a
    non-default palette into whichever test file happens to run next."""
    yield
    theme.apply_theme(theme.DEFAULT_THEME_KEY)


def test_default_theme_is_midnight_dark():
    assert theme.CURRENT_THEME_KEY == theme.DEFAULT_THEME_KEY == "midnight_dark"
    assert theme.get_current_preset().key == "midnight_dark"


def test_every_preset_key_matches_its_dict_key():
    for key, preset in theme.THEME_PRESETS.items():
        assert preset.key == key


def test_at_least_one_light_and_one_dark_preset_exist():
    is_dark_flags = {preset.is_dark for preset in theme.THEME_PRESETS.values()}
    assert True in is_dark_flags
    assert False in is_dark_flags


def test_apply_theme_updates_module_level_colors():
    theme.apply_theme("midnight_dark")

    preset = theme.THEME_PRESETS["midnight_dark"]
    assert theme.COLOR_BG == preset.bg
    assert theme.COLOR_TEXT == preset.text
    assert theme.COLOR_PRIMARY == preset.primary
    assert theme.COLOR_CARD == preset.card
    assert theme.COLOR_STAR == preset.star
    assert theme.CURRENT_THEME_KEY == "midnight_dark"


def test_apply_theme_switches_ctk_appearance_mode():
    import customtkinter as ctk

    theme.apply_theme("midnight_dark")
    assert ctk.get_appearance_mode() == "Dark"

    theme.apply_theme("sunny_light")
    assert ctk.get_appearance_mode() == "Light"


def test_apply_theme_falls_back_to_default_for_unknown_key():
    theme.apply_theme("midnight_dark")
    theme.apply_theme("some_removed_or_typo_key")

    assert theme.CURRENT_THEME_KEY == theme.DEFAULT_THEME_KEY
    assert theme.COLOR_BG == theme.THEME_PRESETS[theme.DEFAULT_THEME_KEY].bg


def test_apply_theme_handles_legacy_light_value():
    # Settings persisted before the preset system used a plain "light"
    # theme value; loading it must not crash, just fall back cleanly.
    theme.apply_theme("light")
    assert theme.CURRENT_THEME_KEY == theme.DEFAULT_THEME_KEY


def test_every_preset_color_is_valid_hex():
    color_fields = (
        "bg", "card", "text", "text_muted", "primary", "primary_hover",
        "success", "success_hover", "warning", "danger", "star",
    )
    for preset in theme.THEME_PRESETS.values():
        for field_name in color_fields:
            value = getattr(preset, field_name)
            assert value.startswith("#") and len(value) == 7
            int(value[1:], 16)  # raises if not valid hex
