"""Shared image assets -- currently just the app icon."""
from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image

ICON_PATH = Path(__file__).resolve().parent.parent.parent / "content" / "images" / "main-icon.png"


def load_icon_image() -> Image.Image:
    return Image.open(ICON_PATH)


def make_ctk_icon(size: int = 32) -> ctk.CTkImage:
    """A CTkImage for embedding the app icon inside a widget (e.g. CTkLabel)."""
    img = load_icon_image()
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
