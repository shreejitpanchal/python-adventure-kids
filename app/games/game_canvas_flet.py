"""The Flet port of the safe drawing surface injected into graphical
lessons as `game`. Preserves the exact public method surface of the old
CTk-based app/games/game_canvas.py -- draw_rect/move_shape/etc. -- so
lesson YAML for the Snake project (lessons 16-18) needs zero changes.

Flet's canvas is declarative/diff-based (a list of Shape objects pushed
whole, not an imperative "canvas.create_rectangle()" API like tk.Canvas),
so this adapter keeps its own id -> Rect mapping and mutates each Rect's
fields directly, then asks the page to sync -- via page.update() rather
than the individual control's own .update(), since a bare control's
update() requires it to already be attached to a live page tree (raises
RuntimeError otherwise), whereas page.update() is always safe to call.

Canvas has no bgcolor of its own, so set_background mutates the wrapping
Container instead. set_title has no real window to retitle now that the
graphical lesson is an inline panel, not a second OS window -- it updates
a Text label inside that panel.
"""
from __future__ import annotations

import asyncio
import math
from typing import Callable, Optional, Protocol

import flet as ft
import flet.canvas as cv

VALID_KEYS = {"Up", "Down", "Left", "Right", "space"}

# Turtle-style drawing starts a little inset from the canvas origin rather
# than at (0, 0), so a lesson's first shape isn't drawn flush against the
# top-left edge and clipped.
_TURTLE_START_X = 50.0
_TURTLE_START_Y = 50.0


class _Updatable(Protocol):
    def update(self) -> None: ...


class GameCanvas:
    def __init__(
        self, canvas: cv.Canvas, container: ft.Container, title_text: ft.Text, page: _Updatable
    ) -> None:
        self._canvas = canvas
        self._container = container
        self._title_text = title_text
        self._page = page
        self._shapes: dict[int, cv.Shape] = {}
        self._sizes: dict[int, tuple[float, float, str]] = {}
        self._next_id = 1
        self._key_handlers: dict[str, Callable[[], None]] = {}
        self._keys_down: set[str] = set()
        self._pending_timers: list[asyncio.TimerHandle] = []
        self._turtle_x = _TURTLE_START_X
        self._turtle_y = _TURTLE_START_Y
        # Degrees, 0 = facing right (+x). Screen y grows downward, so
        # increasing heading turns clockwise as drawn -- exactly what
        # turn_right should do.
        self._turtle_heading = 0.0

    # -- window-ish -------------------------------------------------------------
    def set_title(self, title: str) -> None:
        self._title_text.value = str(title)
        self._page.update()

    def set_background(self, color: str) -> None:
        self._container.bgcolor = str(color)
        self._page.update()

    # -- shapes -------------------------------------------------------------------
    def draw_rect(self, x: int, y: int, width: int, height: int, color: str = "green") -> int:
        """Draws a filled rectangle and returns an id you can move or delete later."""
        shape_id = self._next_id
        self._next_id += 1
        rect = cv.Rect(
            int(x), int(y), int(width), int(height),
            paint=ft.Paint(color=str(color), style=ft.PaintingStyle.FILL),
        )
        self._shapes[shape_id] = rect
        self._sizes[shape_id] = (float(width), float(height), "rect")
        self._canvas.shapes.append(rect)
        self._page.update()
        return shape_id

    def draw_circle(self, x: int, y: int, radius: int, color: str = "green") -> int:
        """Draws a filled circle centered at x, y and returns an id you can
        move, delete, or collide-check later. Center-based, unlike
        draw_rect's top-left x/y -- that's Flet canvas's own Circle
        convention (flet.canvas.Circle), kept as-is rather than papered
        over, since get_shape_position already just reports whatever x/y
        the underlying shape stores."""
        shape_id = self._next_id
        self._next_id += 1
        circle = cv.Circle(
            int(x), int(y), int(radius),
            paint=ft.Paint(color=str(color), style=ft.PaintingStyle.FILL),
        )
        self._shapes[shape_id] = circle
        self._sizes[shape_id] = (float(radius) * 2, float(radius) * 2, "circle")
        self._canvas.shapes.append(circle)
        self._page.update()
        return shape_id

    def move_shape(self, shape_id: int, dx: int, dy: int) -> None:
        """Moves a shape by dx, dy pixels from where it currently is."""
        rect = self._shapes.get(shape_id)
        if rect is None:
            return
        rect.x += int(dx)
        rect.y += int(dy)
        self._page.update()

    def set_shape_position(self, shape_id: int, x: int, y: int) -> None:
        """Moves a shape to an exact x, y position, keeping its size."""
        rect = self._shapes.get(shape_id)
        if rect is None:
            return
        rect.x = int(x)
        rect.y = int(y)
        self._page.update()

    def get_shape_position(self, shape_id: int) -> tuple:
        rect = self._shapes.get(shape_id)
        if rect is None:
            return (0, 0)
        return (rect.x, rect.y)

    def delete_shape(self, shape_id: int) -> None:
        rect = self._shapes.pop(shape_id, None)
        self._sizes.pop(shape_id, None)
        if rect is not None:
            self._canvas.shapes.remove(rect)
            self._page.update()

    def clear(self) -> None:
        self._shapes.clear()
        self._sizes.clear()
        self._canvas.shapes.clear()
        self._page.update()

    def check_collision(self, shape_id_a: int, shape_id_b: int) -> bool:
        """True if the two shapes' axis-aligned bounding boxes overlap --
        for a ball vs. paddle/wall in Arcade Lab lessons. Only shapes drawn
        via draw_rect/draw_circle have a known size (forward()/draw_line's
        lines don't, and aren't meant to be collided with), so an unknown
        id just returns False rather than raising."""
        box_a = self._bounding_box(shape_id_a)
        box_b = self._bounding_box(shape_id_b)
        if box_a is None or box_b is None:
            return False
        ax, ay, aw, ah = box_a
        bx, by, bw, bh = box_b
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def _bounding_box(self, shape_id: int) -> Optional[tuple[float, float, float, float]]:
        shape = self._shapes.get(shape_id)
        size = self._sizes.get(shape_id)
        if shape is None or size is None:
            return None
        width, height, kind = size
        if kind == "circle":
            return (shape.x - width / 2, shape.y - height / 2, width, height)
        return (shape.x, shape.y, width, height)

    # -- turtle-style drawing (Creative Arts track) ------------------------
    def forward(self, distance: int, color: str = "black") -> int:
        """Moves forward by `distance` pixels in the current heading,
        drawing a line along the way. Returns the line's shape id."""
        radians = math.radians(self._turtle_heading)
        new_x = self._turtle_x + math.cos(radians) * distance
        new_y = self._turtle_y + math.sin(radians) * distance

        shape_id = self._next_id
        self._next_id += 1
        line = cv.Line(
            self._turtle_x, self._turtle_y, new_x, new_y,
            paint=ft.Paint(color=str(color), stroke_width=2),
        )
        self._shapes[shape_id] = line
        self._canvas.shapes.append(line)
        self._page.update()

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
        shape_id = self._next_id
        self._next_id += 1
        line = cv.Line(int(x1), int(y1), int(x2), int(y2), paint=ft.Paint(color=str(color), stroke_width=2))
        self._shapes[shape_id] = line
        self._canvas.shapes.append(line)
        self._page.update()
        return shape_id

    # -- animation / input --------------------------------------------------------
    def after(self, ms: int, callback: Callable[[], None]) -> None:
        """Runs callback once, ms milliseconds from now -- call it again inside
        callback for a repeating game loop that never blocks the app.
        Scheduled on the same asyncio loop Flet itself runs on, so it's safe
        to touch this GameCanvas from within callback."""
        loop = asyncio.get_running_loop()
        handle = loop.call_later(ms / 1000, callback)
        self._pending_timers.append(handle)

    def on_key(self, key: str, callback: Callable[[], None]) -> None:
        """Runs callback whenever the given key is pressed. key is one of:
        Up, Down, Left, Right, space. Fed by both a physical keyboard (desktop)
        and an on-screen D-pad (touch) -- see lesson_screen_flet.py."""
        if key not in VALID_KEYS:
            raise ValueError(f"on_key only understands: {', '.join(sorted(VALID_KEYS))}")
        self._key_handlers[key] = callback

    def is_key_down(self, key: str) -> bool:
        """True while `key` is currently held. For continuous movement
        (an Arcade Lab paddle) inside a game.after() tick loop, unlike
        on_key()'s fire-once-per-press callbacks -- Flet's Page-level
        keyboard event only reports key-down, so this is fed by a
        KeyboardListener's separate key-up event instead (see
        lesson_screen_flet.py)."""
        if key not in VALID_KEYS:
            raise ValueError(f"is_key_down only understands: {', '.join(sorted(VALID_KEYS))}")
        return key in self._keys_down

    # -- lifecycle (not part of the lesson-facing `game` API) ----------------------
    def trigger_key(self, key: str) -> None:
        """Called by the on-screen D-pad / physical keyboard handler in
        lesson_screen_flet.py -- not something lesson code calls itself."""
        handler = self._key_handlers.get(key)
        if handler is not None:
            handler()

    def key_down(self, key: str) -> None:
        """Marks `key` as held -- called by the physical keyboard's
        KeyboardListener.on_key_down, not lesson code."""
        if key in VALID_KEYS:
            self._keys_down.add(key)

    def key_up(self, key: str) -> None:
        """Marks `key` as released -- called by KeyboardListener.on_key_up."""
        self._keys_down.discard(key)

    def cancel_pending(self) -> None:
        """Stops any still-scheduled after() callbacks -- called when the
        child navigates away or resets, so a Snake game left mid-animation
        doesn't keep ticking against a detached canvas."""
        for handle in self._pending_timers:
            handle.cancel()
        self._pending_timers.clear()
