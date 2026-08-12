"""Reliable, fast mouse-wheel scrolling for CTkScrollableFrame, installed
ONCE for the whole app (see App.show_frame in app_window.py) rather than
wired up separately in every screen.

CustomTkinter's own wheel handling has two problems:
1. It's bound via `self.bind_all(..., add=True)` in every
   CTkScrollableFrame.__init__ and never unbound in destroy(). Every screen
   here is destroyed and rebuilt on navigation, so each visit leaks one more
   global handler.
2. Its scroll speed depends on `yscrollincrement`, which CTk sets
   inconsistently per instance based on its own DPI-scaling detection --
   the same wheel input could move one frame a lot and another barely at
   all, which read as "scrolling is very slow" (or "only the scrollbar
   works", when the movement was small enough to be imperceptible).

This installs ONE handler that, on each wheel event, walks up from whatever
widget is under the cursor to find the nearest enclosing CTkScrollableFrame
and scrolls it by a fixed, fast *pixel* amount (computed from that frame's
own real content height, not its yscrollincrement) -- consistent speed
everywhere. Re-asserting it (a plain, non-additive bind_all) after every
navigation clears out whatever CTk's own constructors just re-added for the
newly-built screen, so this stays the only handler for the app's lifetime
instead of accumulating one per screen visit.
"""
from __future__ import annotations

import sys

import customtkinter as ctk

_PIXELS_PER_NOTCH = 160  # a snappy, "fast" feel


def _find_enclosing_scrollable_canvas(widget):
    while widget is not None:
        if isinstance(widget, ctk.CTkScrollableFrame):
            return widget._parent_canvas
        widget = getattr(widget, "master", None)
    return None


def _on_wheel(event) -> None:
    canvas = _find_enclosing_scrollable_canvas(event.widget)
    if canvas is None:
        return

    view = canvas.yview()
    if view == (0.0, 1.0):
        return  # nothing to scroll

    bbox = canvas.bbox("all")
    if not bbox:
        return
    content_height = bbox[3] - bbox[1]
    if content_height <= 0:
        return

    if sys.platform == "darwin":
        notches = event.delta
    elif getattr(event, "delta", 0):
        notches = event.delta / 120
    else:
        notches = 1 if getattr(event, "num", 5) == 4 else -1

    new_top = view[0] - (notches * _PIXELS_PER_NOTCH) / content_height
    canvas.yview_moveto(max(0.0, min(1.0, new_top)))


def install_fast_mousewheel_scrolling(root: ctk.CTk) -> None:
    """Call after building/showing a frame -- cheap and safe to call
    repeatedly (e.g. once per navigation); each call re-claims the global
    binding so newly-constructed CTkScrollableFrames' own native handlers
    (just added by their __init__) never get to double-handle the event."""
    root.bind_all("<MouseWheel>", _on_wheel)
    root.bind_all("<Button-4>", _on_wheel)
    root.bind_all("<Button-5>", _on_wheel)
