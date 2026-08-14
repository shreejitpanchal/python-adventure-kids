"""Flet-side color/theme presets.

This is a deliberate duplicate of app/ui/theme.py's ThemePreset registry,
not a shared import -- the live CustomTkinter app keeps working unmodified
throughout this migration (see app/sandbox/inprocess_runner.py's module
docstring for the same pattern applied to the sandbox layer). Once the
Flet UI reaches full feature parity and app/ui/theme.py is deleted, this
file loses its "_flet" suffix and becomes the only copy.

Font note: the CTk app uses "Comic Sans MS", a Windows-installed font that
won't exist on Android. Bundling a replacement font asset is deferred to
the touch/mobile UX pass (a later phase); this file intentionally doesn't
set a font family yet.
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


def get_preset(theme_key: str) -> ThemePreset:
    return THEME_PRESETS.get(theme_key, THEME_PRESETS[DEFAULT_THEME_KEY])
