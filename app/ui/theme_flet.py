"""Flet-side color/theme presets.

This is a deliberate duplicate of app/ui/theme.py's ThemePreset registry,
not a shared import -- the live CustomTkinter app keeps working unmodified
throughout this migration (see app/sandbox/inprocess_runner.py's module
docstring for the same pattern applied to the sandbox layer). Once the
Flet UI reaches full feature parity and app/ui/theme.py is deleted, this
file loses its "_flet" suffix and becomes the only copy.

Font note: the CTk app uses "Comic Sans MS", a Windows-installed font that
won't exist on Android. The Flet app instead bundles "Baloo 2" (Google
Fonts, SIL Open Font License) at assets/fonts/Baloo2-Regular.ttf, registered
and applied globally via page.theme/page.dark_theme in app_window_flet.py's
main() -- so it's set once for the whole app, not per-preset here.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThemePreset:
    key: str
    title: str
    icon: str
    is_dark: bool
    bg: str
    card: str
    text: str
    text_muted: str
    primary: str
    primary_hover: str
    success: str
    success_hover: str
    warning: str
    danger: str
    star: str
    min_level: int = 1
    """Player level (see app.progress.store.PlayerLevel) required to select
    this skin in Settings -- 1 means always unlocked. Locked skins still
    render fine if already selected (e.g. from an old save); the gate is
    only enforced at selection time in the Settings screen."""


THEME_PRESETS: dict[str, ThemePreset] = {
    "sunny_light": ThemePreset(
        key="sunny_light", title="Sunny Light", icon="☀️", is_dark=False,
        bg="#FFF9EE", card="#FFFFFF", text="#2D2A32", text_muted="#6B6873",
        primary="#4F8FF7", primary_hover="#3B72D6",
        success="#3FC97A", success_hover="#2FA863",
        warning="#FFB238", danger="#FF6B6B", star="#FFC93C",
    ),
    "ocean_breeze": ThemePreset(
        key="ocean_breeze", title="Ocean Breeze", icon="🌊", is_dark=False,
        bg="#EAF7FA", card="#FFFFFF", text="#123B4D", text_muted="#5E8592",
        primary="#1FA9C7", primary_hover="#178DA8",
        success="#3FC97A", success_hover="#2FA863",
        warning="#FFB238", danger="#FF6B6B", star="#FFC93C",
    ),
    "sunset_glow": ThemePreset(
        key="sunset_glow", title="Sunset Glow", icon="🌅", is_dark=False,
        bg="#FFF1E6", card="#FFFFFF", text="#4A2E1F", text_muted="#8C6B57",
        primary="#FF8A5B", primary_hover="#E86F41",
        success="#3FC97A", success_hover="#2FA863",
        warning="#FFB238", danger="#FF6B6B", star="#FFC93C",
    ),
    "forest_adventure": ThemePreset(
        key="forest_adventure", title="Forest Adventure", icon="🌲", is_dark=False,
        bg="#EFF7EC", card="#FFFFFF", text="#1F3D2B", text_muted="#5C7C68",
        primary="#3FA65C", primary_hover="#328A4B",
        success="#2FA863", success_hover="#268A52",
        warning="#FFB238", danger="#FF6B6B", star="#FFC93C",
    ),
    "midnight_dark": ThemePreset(
        key="midnight_dark", title="Midnight Dark", icon="🌙", is_dark=True,
        bg="#1A1B26", card="#252735", text="#EDEDF5", text_muted="#9A9AB0",
        primary="#7C9EFF", primary_hover="#6485E0",
        success="#4ADE9E", success_hover="#3BC589",
        warning="#FFC857", danger="#FF7B7B", star="#FFD866",
    ),
    "galaxy": ThemePreset(
        key="galaxy", title="Galaxy", icon="🌌", is_dark=True,
        bg="#1B1130", card="#2A1B47", text="#F1E9FF", text_muted="#B29FD9",
        primary="#C77DFF", primary_hover="#A855F7",
        success="#4ADE9E", success_hover="#3BC589",
        warning="#FFC857", danger="#FF7B7B", star="#FFD866",
    ),
    # Unlockable "Adventure Skins" -- gated behind player level (see
    # app.progress.store.PlayerLevel), not selectable from the start.
    "space_odyssey": ThemePreset(
        key="space_odyssey", title="Space Odyssey", icon="🚀", is_dark=True,
        bg="#0B1026", card="#151B3D", text="#E8ECFF", text_muted="#8A93C7",
        primary="#5DE8FF", primary_hover="#3BC5DD",
        success="#4ADE9E", success_hover="#3BC589",
        warning="#FFC857", danger="#FF6B6B", star="#FFD866",
        min_level=3,
    ),
    "cyberpunk": ThemePreset(
        key="cyberpunk", title="Cyberpunk", icon="🌆", is_dark=True,
        bg="#160221", card="#26073A", text="#F5E6FF", text_muted="#B98FD6",
        primary="#FF2E9A", primary_hover="#E01E82",
        success="#39FF88", success_hover="#2ADB6F",
        warning="#FFE93B", danger="#FF3860", star="#00F0FF",
        min_level=5,
    ),
    "enchanted_forest": ThemePreset(
        key="enchanted_forest", title="Enchanted Forest", icon="🧚", is_dark=True,
        bg="#0D1F16", card="#16301F", text="#E4F5E9", text_muted="#8FBF9F",
        primary="#7CFFB2", primary_hover="#5FE896",
        success="#4ADE9E", success_hover="#3BC589",
        warning="#FFC857", danger="#FF7B7B", star="#FFD866",
        min_level=8,
    ),
}

DEFAULT_THEME_KEY = "midnight_dark"


def get_preset(theme_key: str) -> ThemePreset:
    return THEME_PRESETS.get(theme_key, THEME_PRESETS[DEFAULT_THEME_KEY])


# Semantic keys (not real font names) so the same settings.json value means
# something sensible on both UIs -- see app/config/settings.py's
# Settings.font_family docstring, and app/ui/theme.py's FONT_FAMILY_PRESETS
# for the CTk-side equivalent. "Roboto" needs no bundled .ttf: it's the
# Material/Android default typeface, so Flutter resolves it out of the box
# on every platform this app targets, unlike a Windows-only font name.
FONT_FAMILY_PRESETS: dict[str, str] = {
    "default": "Baloo 2",
    "classic": "Roboto",
}
DEFAULT_FONT_FAMILY_KEY = "default"

# A multiplier applied to every hardcoded text `size=` in the Flet screens
# (there's no central font-size helper the way CTk's theme.py has font_*()
# functions -- every ft.Text/ft.Button call passes its own literal size, so
# each screen computes this once via AppState.font_scale and multiplies).
FONT_SIZE_SCALES: dict[str, float] = {
    "small": 0.85,
    "medium": 1.0,
    "large": 1.2,
    "extra_large": 1.4,
}
DEFAULT_FONT_SIZE_KEY = "medium"


def resolve_font_family(key: str) -> str:
    return FONT_FAMILY_PRESETS.get(key, FONT_FAMILY_PRESETS[DEFAULT_FONT_FAMILY_KEY])


def resolve_font_scale(key: str) -> float:
    return FONT_SIZE_SCALES.get(key, FONT_SIZE_SCALES[DEFAULT_FONT_SIZE_KEY])


def scaled(base_size: int, scale: float) -> int:
    """Multiplies a literal text size by the current font-size scale --
    `size=scaled(15, state.font_scale)` in place of a plain `size=15`."""
    return max(1, round(base_size * scale))
