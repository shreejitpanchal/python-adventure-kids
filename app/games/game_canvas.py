"""The safe drawing surface injected into graphical lessons as `game`.

This is NOT a general Tkinter passthrough — only these specific operations
are exposed, so child code can draw and animate without touching the
filesystem, network, or anything outside this canvas.
"""
from __future__ import annotations

import math
import tkinter as tk
from typing import Callable

VALID_KEYS = {"Up", "Down", "Left", "Right", "space"}

# Turtle-style drawing starts a little inset from the canvas origin rather
# than at (0, 0), so a lesson's first shape isn't drawn flush against the
# top-left edge and clipped.
_TURTLE_START_X = 50.0
_TURTLE_START_Y = 50.0


class GameCanvas:
    def __init__(self, canvas: tk.Canvas, window: tk.Toplevel):
        self._canvas = canvas
        self._window = window
        self._turtle_x = _TURTLE_START_X
        self._turtle_y = _TURTLE_START_Y
        # Degrees, 0 = facing right (+x). Screen y grows downward, so
        # increasing heading turns clockwise as drawn -- exactly what
        # turn_right should do.
        self._turtle_heading = 0.0

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

    # -- turtle-style drawing (Creative Arts track) ------------------------
    def forward(self, distance: int, color: str = "black") -> int:
        """Moves forward by `distance` pixels in the current heading,
        drawing a line along the way. Returns the line's shape id."""
        radians = math.radians(self._turtle_heading)
        new_x = self._turtle_x + math.cos(radians) * distance
        new_y = self._turtle_y + math.sin(radians) * distance
        shape_id = self._canvas.create_line(
            self._turtle_x, self._turtle_y, new_x, new_y, fill=str(color), width=2,
        )
        self._turtle_x, self._turtle_y = new_x, new_y
        return shape_id

    def turn_right(self, degrees: float) -> None:
        """Rotates the heading clockwise (as drawn) by `degrees`."""
        self._turtle_heading = (self._turtle_heading + degrees) % 360

    def turn_left(self, degrees: float) -> None:
        """Rotates the heading counter-clockwise (as drawn) by `degrees`."""
        self._turtle_heading = (self._turtle_heading - degrees) % 360

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: str = "black") -> int:
        """Draws a straight line between two explicit points -- independent
        of forward()/turn_right()'s turtle position and heading."""
        return self._canvas.create_line(int(x1), int(y1), int(x2), int(y2), fill=str(color), width=2)
