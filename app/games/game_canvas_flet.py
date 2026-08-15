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

# Robot Adventure: grid directions as (delta_col, delta_row), and the
# left/right 90-degree turn tables -- a fixed cardinal-direction snap,
# distinct from the turtle's continuous-degree heading above.
_DIRECTION_DELTA = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}
_LEFT_TURN = {"N": "W", "W": "S", "S": "E", "E": "N"}
_RIGHT_TURN = {"N": "E", "E": "S", "S": "W", "W": "N"}


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

        # Robot Adventure grid-world state -- all None/empty until
        # create_grid()/place_robot() are called by a lesson.
        self._grid_cols = 0
        self._grid_rows = 0
        self._cell_size = 50
        self._walls: set[tuple[tuple[int, int], tuple[int, int]]] = set()
        self._obstacles: set[tuple[int, int]] = set()
        self._goal: Optional[tuple[int, int]] = None
        self._coin_shapes: dict[tuple[int, int], int] = {}
        self._coins_collected = 0
        self._robot_col = 0
        self._robot_row = 0
        self._robot_facing = "E"
        self._robot_body_id: Optional[int] = None
        self._robot_nose_id: Optional[int] = None

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

    # -- Robot Adventure: grid world -----------------------------------------------
    def create_grid(self, cols: int, rows: int, cell_size: int = 50) -> None:
        """Sets up a cols x rows grid the robot moves around on, drawing
        faint gridlines. Call once, before place_robot()/place_wall()/etc."""
        self._grid_cols = cols
        self._grid_rows = rows
        self._cell_size = cell_size
        width, height = cols * cell_size, rows * cell_size
        for row in range(rows + 1):
            y = row * cell_size
            self.draw_line(0, y, width, y, "#3A3A4E")
        for col in range(cols + 1):
            x = col * cell_size
            self.draw_line(x, 0, x, height, "#3A3A4E")

    def place_robot(self, col: int, row: int, facing: str = "E") -> None:
        """Places the robot at (col, row), facing one of N/E/S/W. Drawn as
        a colored square body plus a small circle "nose" on the leading
        edge to show facing direction -- this canvas has no rotatable
        sprite, so a rotating body isn't an option."""
        self._robot_col, self._robot_row = col, row
        self._robot_facing = facing
        cell = self._cell_size
        self._robot_body_id = self.draw_rect(
            col * cell + 8, row * cell + 8, cell - 16, cell - 16, "#00E5FF",
        )
        nose_x, nose_y = self._nose_position()
        self._robot_nose_id = self.draw_circle(nose_x, nose_y, 5, "white")

    def _nose_position(self) -> tuple[float, float]:
        cell = self._cell_size
        cx = self._robot_col * cell + cell / 2
        cy = self._robot_row * cell + cell / 2
        offset = cell / 2 - 6
        dcol, drow = _DIRECTION_DELTA[self._robot_facing]
        return cx + dcol * offset, cy + drow * offset

    def _sync_robot_shapes(self) -> None:
        cell = self._cell_size
        if self._robot_body_id is not None:
            self.set_shape_position(self._robot_body_id, self._robot_col * cell + 8, self._robot_row * cell + 8)
        if self._robot_nose_id is not None:
            nose_x, nose_y = self._nose_position()
            self.set_shape_position(self._robot_nose_id, nose_x, nose_y)

    def robot_forward(self) -> bool:
        """Moves the robot one cell in the direction it's facing, if
        nothing blocks the way. Returns whether it actually moved -- a
        blocked move is a silent no-op, not an error, matching this app's
        forgiving-by-default philosophy elsewhere (e.g. trigger_key on an
        unregistered key)."""
        if self.robot_wall_ahead():
            return False
        dcol, drow = _DIRECTION_DELTA[self._robot_facing]
        self._robot_col += dcol
        self._robot_row += drow
        self._sync_robot_shapes()
        self._maybe_collect_coin()
        return True

    def robot_turn_left(self) -> None:
        """Rotates the robot's facing 90 degrees counter-clockwise
        (N->W->S->E->N). A fixed grid-snapped turn -- see turn_left() for
        the turtle's separate continuous-degree turning."""
        self._robot_facing = _LEFT_TURN[self._robot_facing]
        self._sync_robot_shapes()

    def robot_turn_right(self) -> None:
        """Rotates the robot's facing 90 degrees clockwise (N->E->S->W->N)."""
        self._robot_facing = _RIGHT_TURN[self._robot_facing]
        self._sync_robot_shapes()

    def robot_wall_ahead(self) -> bool:
        """True if the cell the robot is facing is blocked -- a wall, an
        obstacle, or the edge of the grid -- without moving."""
        dcol, drow = _DIRECTION_DELTA[self._robot_facing]
        new_col, new_row = self._robot_col + dcol, self._robot_row + drow
        if not (0 <= new_col < self._grid_cols and 0 <= new_row < self._grid_rows):
            return True
        if (new_col, new_row) in self._obstacles:
            return True
        edge = self._normalize_edge((self._robot_col, self._robot_row), (new_col, new_row))
        return edge in self._walls

    @staticmethod
    def _normalize_edge(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
        return (a, b) if a <= b else (b, a)

    def place_wall(self, col: int, row: int, side: str) -> None:
        """Blocks movement between (col, row) and its neighbor on `side`
        (N/E/S/W), and draws a visible wall segment there."""
        dcol, drow = _DIRECTION_DELTA[side]
        other = (col + dcol, row + drow)
        self._walls.add(self._normalize_edge((col, row), other))

        cell = self._cell_size
        x0, y0 = col * cell, row * cell
        if side == "N":
            self.draw_line(x0, y0, x0 + cell, y0, "#FF6B6B")
        elif side == "S":
            self.draw_line(x0, y0 + cell, x0 + cell, y0 + cell, "#FF6B6B")
        elif side == "W":
            self.draw_line(x0, y0, x0, y0 + cell, "#FF6B6B")
        elif side == "E":
            self.draw_line(x0 + cell, y0, x0 + cell, y0 + cell, "#FF6B6B")

    def place_obstacle(self, col: int, row: int) -> None:
        """Marks (col, row) as blocked and draws a gray block there."""
        self._obstacles.add((col, row))
        cell = self._cell_size
        self.draw_rect(col * cell + 4, row * cell + 4, cell - 8, cell - 8, "#555555")

    def place_goal(self, col: int, row: int) -> None:
        """Marks (col, row) as the mission's target and draws a gold marker."""
        self._goal = (col, row)
        cell = self._cell_size
        cx, cy = col * cell + cell / 2, row * cell + cell / 2
        self.draw_circle(cx, cy, cell / 3, "gold")

    def robot_at_goal(self) -> bool:
        return (self._robot_col, self._robot_row) == self._goal

    def place_coin(self, col: int, row: int) -> None:
        """Adds a collectible coin at (col, row) -- auto-collected (and
        removed) the moment the robot moves onto that cell."""
        cell = self._cell_size
        cx, cy = col * cell + cell / 2, row * cell + cell / 2
        shape_id = self.draw_circle(cx, cy, cell / 5, "yellow")
        self._coin_shapes[(col, row)] = shape_id

    def _maybe_collect_coin(self) -> None:
        shape_id = self._coin_shapes.pop((self._robot_col, self._robot_row), None)
        if shape_id is not None:
            self.delete_shape(shape_id)
            self._coins_collected += 1

    def coins_collected(self) -> int:
        return self._coins_collected

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
