"""Shared image assets -- the app icon (window/taskbar + in-UI)."""
from __future__ import annotations

import sys
from pathlib import Path

import customtkinter as ctk
from PIL import Image

_IMAGES_DIR = Path(__file__).resolve().parent.parent.parent / "content" / "images"
ICON_PATH = _IMAGES_DIR / "main-icon.png"
ICON_ICO_PATH = _IMAGES_DIR / "main-icon.ico"

# Windows groups taskbar buttons/icons by this ID. Without setting one, a
# Python-launched app inherits python.exe's own default identity, which is
# exactly why the taskbar can keep showing the generic Python icon even
# after the window's own icon has been changed.
APP_USER_MODEL_ID = "PythonAdventure.KidsLearningApp.1"


def load_icon_image() -> Image.Image:
    return Image.open(ICON_PATH)


def make_ctk_icon(size: int = 32) -> ctk.CTkImage:
    """A CTkImage for embedding the app icon inside a widget (e.g. CTkLabel)."""
    img = load_icon_image()
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


def ensure_windows_app_id() -> None:
    """Registers a distinct AppUserModelID so Windows' taskbar treats this as
    its own application rather than grouping it under python.exe's identity.
    Must be called before the first window is shown. No-op off Windows."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except (AttributeError, OSError):
        pass


def apply_window_icon(window) -> None:
    """Sets both the title-bar icon (iconphoto, works everywhere) and the
    native .ico (iconbitmap, which Windows' taskbar respects more reliably
    than iconphoto alone)."""
    from PIL import ImageTk

    window._window_icon_photo = ImageTk.PhotoImage(load_icon_image())
    window.iconphoto(True, window._window_icon_photo)

    if sys.platform == "win32" and ICON_ICO_PATH.exists():
        try:
            window.iconbitmap(default=str(ICON_ICO_PATH))
        except Exception:
            pass
