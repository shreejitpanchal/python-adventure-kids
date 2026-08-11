"""Shared colors, fonts, and sizing for the child-friendly UI."""
from __future__ import annotations

import customtkinter as ctk

# Bright, friendly palette
COLOR_BG = "#FFF9EE"
COLOR_PRIMARY = "#4F8FF7"
COLOR_PRIMARY_HOVER = "#3B72D6"
COLOR_SUCCESS = "#3FC97A"
COLOR_SUCCESS_HOVER = "#2FA863"
COLOR_WARNING = "#FFB238"
COLOR_DANGER = "#FF6B6B"
COLOR_TEXT = "#2D2A32"
COLOR_TEXT_MUTED = "#6B6873"
COLOR_CARD = "#FFFFFF"
COLOR_STAR = "#FFC93C"

FONT_FAMILY = "Comic Sans MS"

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700


def apply_base_theme() -> None:
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


def font_title(size: int = 34) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold")


def font_heading(size: int = 22) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold")


def font_body(size: int = 16) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size)


def font_button(size: int = 20) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold")
