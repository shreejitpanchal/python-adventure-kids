"""Shared colors, fonts, and sizing for the child-friendly UI.

Colors are mutable module attributes, not constants -- apply_theme()
reassigns them, and every screen reads theme.COLOR_X fresh each time it's
built (screens are destroyed/rebuilt on navigation, see app_window.py), so
switching the palette and re-showing the current screen is all it takes to
pick up a new theme everywhere, without threading a theme object through
every widget.
"""
from __future__ import annotations

from dataclasses import dataclass

import customtkinter as ctk


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


# A handful of curated, kid-friendly palettes -- including two dark-mode
# options. Order here is the order they're shown in the Settings screen.
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
}

DEFAULT_THEME_KEY = "midnight_dark"
CURRENT_THEME_KEY = DEFAULT_THEME_KEY

# Populated by apply_theme() below -- these are the names every screen
# actually imports and reads (as `theme.COLOR_X`).
COLOR_BG: str
COLOR_PRIMARY: str
COLOR_PRIMARY_HOVER: str
COLOR_SUCCESS: str
COLOR_SUCCESS_HOVER: str
COLOR_WARNING: str
COLOR_DANGER: str
COLOR_TEXT: str
COLOR_TEXT_MUTED: str
COLOR_CARD: str
COLOR_STAR: str

FONT_FAMILY = "Comic Sans MS"

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700


def apply_base_theme() -> None:
    ctk.set_default_color_theme("blue")


def get_current_preset() -> ThemePreset:
    return THEME_PRESETS[CURRENT_THEME_KEY]


def apply_theme(theme_key: str) -> None:
    """Switches the active color palette (falls back to the default for an
    unrecognized key, e.g. old settings.json values). Also updates CTk's own
    light/dark appearance mode, for the built-in widget chrome we don't
    explicitly color ourselves. Doesn't repaint anything already on screen
    -- the caller re-shows the current screen for that (see
    App.apply_and_persist_theme)."""
    global COLOR_BG, COLOR_PRIMARY, COLOR_PRIMARY_HOVER, COLOR_SUCCESS
    global COLOR_SUCCESS_HOVER, COLOR_WARNING, COLOR_DANGER, COLOR_TEXT
    global COLOR_TEXT_MUTED, COLOR_CARD, COLOR_STAR, CURRENT_THEME_KEY

    preset = THEME_PRESETS.get(theme_key, THEME_PRESETS[DEFAULT_THEME_KEY])

    COLOR_BG = preset.bg
    COLOR_PRIMARY = preset.primary
    COLOR_PRIMARY_HOVER = preset.primary_hover
    COLOR_SUCCESS = preset.success
    COLOR_SUCCESS_HOVER = preset.success_hover
    COLOR_WARNING = preset.warning
    COLOR_DANGER = preset.danger
    COLOR_TEXT = preset.text
    COLOR_TEXT_MUTED = preset.text_muted
    COLOR_CARD = preset.card
    COLOR_STAR = preset.star
    CURRENT_THEME_KEY = preset.key

    ctk.set_appearance_mode("dark" if preset.is_dark else "light")


# Seed the module-level colors so anything importing theme before the App
# calls apply_theme() (e.g. a test, or a standalone widget probe) still
# gets a valid default palette instead of NameError.
apply_theme(DEFAULT_THEME_KEY)


def font_title(size: int = 34) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold")


def font_heading(size: int = 22) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold")


def font_body(size: int = 16) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size)


def font_button(size: int = 20) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold")
