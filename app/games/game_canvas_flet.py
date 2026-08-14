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
from typing import Callable, Optional, Protocol

import flet as ft
import flet.canvas as cv

VALID_KEYS = {"Up", "Down", "Left", "Right", "space"}


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
        self._shapes: dict[int, cv.Rect] = {}
        self._next_id = 1
        self._key_handlers: dict[str, Callable[[], None]] = {}
        self._pending_timers: list[asyncio.TimerHandle] = []

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
        self._canvas.shapes.append(rect)
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
        if rect is not None:
            self._canvas.shapes.remove(rect)
            self._page.update()

    def clear(self) -> None:
        self._shapes.clear()
        self._canvas.shapes.clear()
        self._page.update()

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

    # -- lifecycle (not part of the lesson-facing `game` API) ----------------------
    def trigger_key(self, key: str) -> None:
        """Called by the on-screen D-pad / physical keyboard handler in
        lesson_screen_flet.py -- not something lesson code calls itself."""
        handler = self._key_handlers.get(key)
        if handler is not None:
            handler()

    def cancel_pending(self) -> None:
        """Stops any still-scheduled after() callbacks -- called when the
        child navigates away or resets, so a Snake game left mid-animation
        doesn't keep ticking against a detached canvas."""
        for handle in self._pending_timers:
            handle.cancel()
        self._pending_timers.clear()
