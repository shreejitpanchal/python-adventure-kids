import pytest

from app.ui import theme


@pytest.fixture(autouse=True)
def _restore_default_theme():
    """apply_theme() mutates module-level globals, so tests must not leak a
    non-default palette into whichever test file happens to run next."""
    yield
    theme.apply_theme(theme.DEFAULT_THEME_KEY)


@pytest.fixture(autouse=True)
def _restore_default_font():
    """apply_font() mutates module-level globals the same way apply_theme()
    does -- same leak risk, same fix."""
    yield
    theme.apply_font(theme.DEFAULT_FONT_FAMILY_KEY, theme.DEFAULT_FONT_SIZE_KEY)


def test_default_theme_is_forest_adventure():
    assert theme.CURRENT_THEME_KEY == theme.DEFAULT_THEME_KEY == "forest_adventure"
    assert theme.get_current_preset().key == "forest_adventure"


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


# -- every skin is unlocked from the start -------------------------------------
_ALL_SKIN_KEYS = {
    "sunny_light", "ocean_breeze", "sunset_glow", "forest_adventure", "midnight_dark", "galaxy",
    "space_odyssey", "cyberpunk", "enchanted_forest",
}


def test_every_preset_is_unlocked_from_the_start():
    for key in _ALL_SKIN_KEYS:
        assert theme.THEME_PRESETS[key].min_level == 1


def test_every_preset_key_set_matches_the_full_skin_list():
    assert set(theme.THEME_PRESETS.keys()) == _ALL_SKIN_KEYS


# -- font family + size -------------------------------------------------------
def test_default_font_is_large_comic_sans():
    assert theme.CURRENT_FONT_FAMILY_KEY == theme.DEFAULT_FONT_FAMILY_KEY == "default"
    assert theme.CURRENT_FONT_SIZE_KEY == theme.DEFAULT_FONT_SIZE_KEY == "large"
    assert theme.FONT_FAMILY == "Comic Sans MS"
    assert theme.FONT_SIZE_SCALE == 1.2


def test_apply_font_updates_family_and_scale():
    theme.apply_font("classic", "small")
    assert theme.FONT_FAMILY == "Segoe UI"
    assert theme.FONT_SIZE_SCALE == 0.85
    assert theme.CURRENT_FONT_FAMILY_KEY == "classic"
    assert theme.CURRENT_FONT_SIZE_KEY == "small"


def test_apply_font_falls_back_to_defaults_for_unknown_keys():
    theme.apply_font("not_a_real_family", "not_a_real_size")
    assert theme.CURRENT_FONT_FAMILY_KEY == theme.DEFAULT_FONT_FAMILY_KEY
    assert theme.CURRENT_FONT_SIZE_KEY == theme.DEFAULT_FONT_SIZE_KEY
    assert theme.FONT_FAMILY == "Comic Sans MS"
    assert theme.FONT_SIZE_SCALE == 1.2


@pytest.fixture
def tk_root():
    """CTkFont requires a live default Tk root to exist -- the rest of this
    test file never constructs one (only reads plain module globals), but
    these font_*() tests build real CTkFont objects, matching the pattern
    used elsewhere in this suite for widgets that need a real Tk root
    (e.g. test_snake_lessons.py's game_canvas fixture)."""
    import customtkinter as ctk

    root = ctk.CTk()
    root.withdraw()
    yield root
    root.destroy()


def test_font_helpers_scale_their_size_argument(tk_root):
    theme.apply_font("default", "large")  # 1.2x
    assert theme.font_body(16).cget("size") == round(16 * 1.2)
    assert theme.font_heading(20).cget("size") == round(20 * 1.2)
    assert theme.font_title(34).cget("size") == round(34 * 1.2)
    assert theme.font_button(20).cget("size") == round(20 * 1.2)


def test_font_helpers_use_the_current_family_except_mono(tk_root):
    theme.apply_font("classic", "medium")
    assert theme.font_body(16).cget("family") == "Segoe UI"
    assert theme.font_heading(16).cget("family") == "Segoe UI"


def test_font_mono_always_stays_consolas_but_still_scales(tk_root):
    theme.apply_font("classic", "extra_large")  # 1.4x, family should be ignored
    mono = theme.font_mono(15)
    assert mono.cget("family") == "Consolas"
    assert mono.cget("size") == round(15 * 1.4)


def test_font_size_scale_never_rounds_down_to_zero():
    theme.apply_font("default", "small")
    assert theme._scaled(1) >= 1
