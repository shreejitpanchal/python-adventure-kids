"""The safe drawing surface injected into graphical lessons as `game`.

This is NOT a general Tkinter passthrough — only these specific operations
are exposed, so child code can draw and animate without touching the
filesystem, network, or anything outside this canvas.
"""
from __future__ import annotations

import tkinter as tk
from typing import Callable

VALID_KEYS = {"Up", "Down", "Left", "Right", "space"}


class GameCanvas:
    def __init__(self, canvas: tk.Canvas, window: tk.Toplevel):
        self._canvas = canvas
        self._window = window

    def set_title(self, title: str) -> None:
        self._window.title(str(title))

    def set_background(self, color: str) -> None:
        self._canvas.configure(bg=str(color))

    def draw_rect(self, x: int, y: int, width: int, height: int, color: str = "green") -> int:
        """Draws a filled rectangle and returns an id you can move or delete later."""
        return self._canvas.create_rectangle(
            int(x), int(y), int(x) + int(width), int(y) + int(height),
            fill=str(color), outline="",
        )

    def move_shape(self, shape_id: int, dx: int, dy: int) -> None:
        """Moves a shape by dx, dy pixels from where it currently is."""
        self._canvas.move(shape_id, int(dx), int(dy))

    def set_shape_position(self, shape_id: int, x: int, y: int) -> None:
        """Moves a shape to an exact x, y position, keeping its size."""
        coords = self._canvas.coords(shape_id)
        width = coords[2] - coords[0]
        height = coords[3] - coords[1]
        self._canvas.coords(shape_id, x, y, x + width, y + height)

    def get_shape_position(self, shape_id: int) -> tuple:
        coords = self._canvas.coords(shape_id)
        return (coords[0], coords[1])

    def delete_shape(self, shape_id: int) -> None:
        self._canvas.delete(shape_id)

    def clear(self) -> None:
        self._canvas.delete("all")

    def after(self, ms: int, callback: Callable[[], None]) -> None:
        """Runs callback once, ms milliseconds from now -- call it again inside
        callback for a repeating game loop that never blocks the window."""
        self._canvas.after(int(ms), callback)

    def on_key(self, key: str, callback: Callable[[], None]) -> None:
        """Runs callback whenever the given key is pressed. key is one of:
        Up, Down, Left, Right, space."""
        if key not in VALID_KEYS:
            raise ValueError(f"on_key only understands: {', '.join(sorted(VALID_KEYS))}")
        sequence = "<space>" if key == "space" else f"<{key}>"
        self._window.bind(sequence, lambda event: callback())
        self._canvas.focus_set()
