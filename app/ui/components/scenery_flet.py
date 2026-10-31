"""Drawn scenery for the Flet game world -- vector art on flet.canvas
instead of emoji: a horizon silhouette per World (castle towers, snowy
peaks, rolling hills, island waves, swamp reeds, the scholar's tower, an
observatory dome) plus scattered foreground motifs (trees, palms,
mushrooms, stars) behind each map road, and the same horizon as a skyline
strip along the bottom of hero headers.

Everything is plain cv.Path/cv.Rect/cv.Circle/cv.Arc shapes in the
World's own color at low alpha, so the road and nodes drawn over it stay
legible. Motif positions come from a seeded RNG (the world id) so a scene
is stable across rebuilds and unit-testable. Flet only; no image assets,
so adding a World never needs an asset pipeline -- a World without an
entry here gets the "meadow" scene.
"""
from __future__ import annotations

import math
import random
from typing import Callable, Optional

import flet as ft
import flet.canvas as cv

from app.ui.color_utils import darken, lighten, with_alpha

HORIZON_HEIGHT = 110.0
SKYLINE_HEIGHT = 56.0
# Hero headers fill the screen width, which the Python side never knows;
# the skyline is drawn across this virtual width and clipped by the band.
SKYLINE_VIRTUAL_WIDTH = 1400.0
MOTIF_ALPHA = 0.38
HORIZON_ALPHA = 0.30
GROUND_ALPHA = 0.08

WORLD_SCENES: dict[str, str] = {
    "number_kingdom": "castle",
    "word_valley": "valley",
    "logic_peaks": "peaks",
    "arcade_islands": "islands",
    "bug_swamp": "swamp",
    "scholar_tower": "tower",
    "ai_observatory": "observatory",
}
DEFAULT_SCENE = "meadow"


def scene_for_world(world_id: str) -> str:
    return WORLD_SCENES.get(world_id, DEFAULT_SCENE)


def _fill(color: str, alpha: float) -> ft.Paint:
    return ft.Paint(color=with_alpha(color, alpha), style=ft.PaintingStyle.FILL)


def _stroke(color: str, alpha: float, width: float = 3) -> ft.Paint:
    return ft.Paint(color=with_alpha(color, alpha), style=ft.PaintingStyle.STROKE, stroke_width=width)


def _polygon(points: list[tuple[float, float]], paint: ft.Paint) -> cv.Path:
    elements: list = [cv.Path.MoveTo(*points[0])]
    elements.extend(cv.Path.LineTo(x, y) for x, y in points[1:])
    elements.append(cv.Path.Close())
    return cv.Path(elements, paint=paint)


# -- horizons --------------------------------------------------------------------------------
def _castle_horizon(width: float, height: float, color: str) -> list:
    shapes: list = []
    paint = _fill(color, HORIZON_ALPHA)
    x = 0.0
    tall = True
    while x < width:
        tower_w = 42.0 if tall else 30.0
        tower_h = height * (0.9 if tall else 0.55)
        top = height - tower_h
        shapes.append(cv.Rect(x, top, tower_w, tower_h, paint=paint))
        # Crenellations along the top edge.
        notch = tower_w / 5
        for i in range(0, 5, 2):
            shapes.append(cv.Rect(x + i * notch, top - notch * 0.8, notch, notch * 0.8, paint=paint))
        if tall:
            shapes.append(cv.Line(x + tower_w / 2, top - notch, x + tower_w / 2, top - notch - 18, paint=_stroke(color, HORIZON_ALPHA, 2)))
            shapes.append(_polygon([(x + tower_w / 2, top - notch - 18), (x + tower_w / 2 + 14, top - notch - 13), (x + tower_w / 2, top - notch - 8)], paint))
        # A curtain wall between towers.
        shapes.append(cv.Rect(x + tower_w, height - height * 0.35, 26, height * 0.35, paint=paint))
        x += tower_w + 26
        tall = not tall
    return shapes


def _peaks_horizon(width: float, height: float, color: str) -> list:
    shapes: list = []
    paint = _fill(color, HORIZON_ALPHA)
    snow = _fill("#FFFFFF", 0.55)
    x = -40.0
    tall = True
    while x < width + 40:
        peak_w = 150.0 if tall else 100.0
        peak_h = height if tall else height * 0.65
        apex = (x + peak_w / 2, height - peak_h)
        shapes.append(_polygon([(x, height), apex, (x + peak_w, height)], paint))
        cap = peak_h * 0.28
        shapes.append(_polygon([
            (apex[0] - cap * 0.75, apex[1] + cap), apex, (apex[0] + cap * 0.75, apex[1] + cap),
            (apex[0] + cap * 0.4, apex[1] + cap * 0.75), (apex[0], apex[1] + cap * 1.05), (apex[0] - cap * 0.4, apex[1] + cap * 0.75),
        ], snow))
        x += peak_w * 0.7
        tall = not tall
    return shapes


def _valley_horizon(width: float, height: float, color: str) -> list:
    shapes: list = []
    for layer, (alpha, lift) in enumerate(((HORIZON_ALPHA * 0.6, 0.35), (HORIZON_ALPHA, 0.6))):
        elements: list = [cv.Path.MoveTo(0, height)]
        x = 0.0
        hill_w = 180.0 - layer * 50
        up = True
        elements.append(cv.Path.LineTo(0, height - height * lift * 0.5))
        while x < width + hill_w:
            y = height - height * (lift if up else lift * 0.45)
            elements.append(cv.Path.QuadraticTo(x + hill_w / 2, y, x + hill_w, height - height * lift * 0.5))
            x += hill_w
            up = not up
        elements.append(cv.Path.LineTo(x, height))
        elements.append(cv.Path.Close())
        shapes.append(cv.Path(elements, paint=_fill(color, alpha)))
    return shapes


def _islands_horizon(width: float, height: float, color: str) -> list:
    shapes: list = []
    water = _fill(color, HORIZON_ALPHA * 0.8)
    shapes.append(cv.Rect(0, height * 0.55, width, height * 0.45, paint=water))
    # Wave crests as a stroked, scalloped line.
    elements: list = [cv.Path.MoveTo(0, height * 0.62)]
    x = 0.0
    while x < width:
        elements.append(cv.Path.QuadraticTo(x + 15, height * 0.52, x + 30, height * 0.62))
        x += 30
    shapes.append(cv.Path(elements, paint=_stroke("#FFFFFF", 0.5, 2)))
    # Island humps with a sun-bleached top.
    for cx in (width * 0.2, width * 0.62, width * 0.95):
        shapes.append(cv.Arc(cx - 60, height * 0.35, 120, height * 0.5, math.pi, math.pi, use_center=True, paint=_fill(color, HORIZON_ALPHA)))
    return shapes


def _swamp_horizon(width: float, height: float, color: str) -> list:
    shapes: list = [cv.Rect(0, height * 0.6, width, height * 0.4, paint=_fill(color, HORIZON_ALPHA * 0.7))]
    x = 10.0
    while x < width:
        base = height * 0.6
        for dx, h in ((0, 46), (7, 60), (14, 40)):
            shapes.append(cv.Line(x + dx, base, x + dx + 2, base - h, paint=_stroke(darken(color, 0.1), HORIZON_ALPHA, 3)))
        shapes.append(cv.Oval(x + 24, base + 10, 26, 10, paint=_fill(lighten(color, 0.2), HORIZON_ALPHA)))
        x += 70
    return shapes


def _tower_horizon(width: float, height: float, color: str) -> list:
    shapes: list = []
    paint = _fill(color, HORIZON_ALPHA)
    x = 30.0
    big = True
    while x < width:
        tower_w = 48.0 if big else 24.0
        tower_h = height if big else height * 0.5
        top = height - tower_h
        shapes.append(cv.Rect(x, top, tower_w, tower_h, paint=paint))
        shapes.append(_polygon([(x - 6, top), (x + tower_w / 2, top - tower_w * 0.7), (x + tower_w + 6, top)], paint))
        if big:
            for row in range(3):
                shapes.append(cv.Rect(x + tower_w / 2 - 5, top + 18 + row * 26, 10, 14, border_radius=5, paint=_fill("#FFFFFF", 0.5)))
        x += tower_w + 34
        big = not big
    return shapes


def _observatory_horizon(width: float, height: float, color: str) -> list:
    shapes: list = []
    paint = _fill(color, HORIZON_ALPHA)
    x = 0.0
    while x < width:
        dome_w = 120.0
        shapes.append(cv.Rect(x + 15, height * 0.55, dome_w - 30, height * 0.45, paint=paint))
        shapes.append(cv.Arc(x, height * 0.15, dome_w, height * 0.8, math.pi, math.pi, use_center=True, paint=paint))
        shapes.append(cv.Rect(x + dome_w / 2 - 5, height * 0.18, 10, height * 0.3, paint=_fill("#FFFFFF", 0.45)))
        # A ringed planet over every other dome.
        if int(x // dome_w) % 2 == 0:
            shapes.append(cv.Circle(x + dome_w + 60, height * 0.25, 12, paint=_fill(lighten(color, 0.3), HORIZON_ALPHA)))
            shapes.append(cv.Oval(x + dome_w + 40, height * 0.25 - 5, 40, 10, paint=_stroke(lighten(color, 0.3), HORIZON_ALPHA, 2)))
        x += dome_w + 120
    return shapes


def _meadow_horizon(width: float, height: float, color: str) -> list:
    return _valley_horizon(width, height, color)


_HORIZONS: dict[str, Callable[[float, float, str], list]] = {
    "castle": _castle_horizon,
    "peaks": _peaks_horizon,
    "valley": _valley_horizon,
    "islands": _islands_horizon,
    "swamp": _swamp_horizon,
    "tower": _tower_horizon,
    "observatory": _observatory_horizon,
    "meadow": _meadow_horizon,
}


def horizon_shapes(scene: str, width: float, height: float, color: str) -> list:
    return _HORIZONS.get(scene, _meadow_horizon)(width, height, color)


# -- motifs -------------------------------------------------------------------------------
def _round_tree(x: float, y: float, s: float, color: str) -> list:
    return [
        cv.Rect(x - s * 0.08, y - s * 0.3, s * 0.16, s * 0.5, paint=_fill(darken(color, 0.3), MOTIF_ALPHA)),
        cv.Circle(x, y - s * 0.5, s * 0.4, paint=_fill(color, MOTIF_ALPHA)),
    ]


def _pine(x: float, y: float, s: float, color: str) -> list:
    paint = _fill(color, MOTIF_ALPHA)
    return [
        cv.Rect(x - s * 0.06, y - s * 0.15, s * 0.12, s * 0.35, paint=_fill(darken(color, 0.3), MOTIF_ALPHA)),
        _polygon([(x - s * 0.4, y - s * 0.1), (x, y - s * 0.7), (x + s * 0.4, y - s * 0.1)], paint),
        _polygon([(x - s * 0.3, y - s * 0.5), (x, y - s), (x + s * 0.3, y - s * 0.5)], paint),
    ]


def _palm(x: float, y: float, s: float, color: str) -> list:
    shapes: list = [cv.Path([cv.Path.MoveTo(x, y), cv.Path.QuadraticTo(x + s * 0.3, y - s * 0.5, x + s * 0.15, y - s)], paint=_stroke(darken(color, 0.3), MOTIF_ALPHA, 4))]
    top = (x + s * 0.15, y - s)
    for angle in (-2.6, -2.0, -1.2, -0.5, 0.2):
        shapes.append(cv.Path(
            [cv.Path.MoveTo(*top), cv.Path.QuadraticTo(top[0] + math.cos(angle) * s * 0.3, top[1] + math.sin(angle) * s * 0.2 - s * 0.15, top[0] + math.cos(angle) * s * 0.55, top[1] + math.sin(angle) * s * 0.35)],
            paint=_stroke(color, MOTIF_ALPHA, 3),
        ))
    return shapes


def _mushroom(x: float, y: float, s: float, color: str) -> list:
    return [
        cv.Rect(x - s * 0.12, y - s * 0.4, s * 0.24, s * 0.4, border_radius=4, paint=_fill("#F5E6D3", MOTIF_ALPHA + 0.2)),
        cv.Arc(x - s * 0.4, y - s * 0.8, s * 0.8, s * 0.8, math.pi, math.pi, use_center=True, paint=_fill(color, MOTIF_ALPHA + 0.1)),
        cv.Circle(x - s * 0.15, y - s * 0.55, s * 0.06, paint=_fill("#FFFFFF", 0.6)),
        cv.Circle(x + s * 0.12, y - s * 0.62, s * 0.05, paint=_fill("#FFFFFF", 0.6)),
    ]


def _star(x: float, y: float, s: float, color: str) -> list:
    points = []
    for i in range(10):
        radius = s * 0.4 if i % 2 == 0 else s * 0.17
        angle = -math.pi / 2 + i * math.pi / 5
        points.append((x + math.cos(angle) * radius, y + math.sin(angle) * radius))
    return [_polygon(points, _fill(lighten(color, 0.3), MOTIF_ALPHA + 0.1))]


def _gem(x: float, y: float, s: float, color: str) -> list:
    return [
        _polygon([(x - s * 0.35, y - s * 0.45), (x + s * 0.35, y - s * 0.45), (x + s * 0.5, y - s * 0.2), (x, y + s * 0.3), (x - s * 0.5, y - s * 0.2)], _fill(color, MOTIF_ALPHA + 0.1)),
        cv.Line(x - s * 0.5, y - s * 0.2, x + s * 0.5, y - s * 0.2, paint=_stroke("#FFFFFF", 0.5, 1.5)),
    ]


def _book_stack(x: float, y: float, s: float, color: str) -> list:
    return [
        cv.Rect(x - s * 0.35, y - h, s * 0.7, s * 0.14, border_radius=3, paint=_fill(shade, MOTIF_ALPHA))
        for h, shade in ((s * 0.14, color), (s * 0.3, lighten(color, 0.25)), (s * 0.46, darken(color, 0.15)))
    ]


def _planet(x: float, y: float, s: float, color: str) -> list:
    return [
        cv.Circle(x, y - s * 0.4, s * 0.28, paint=_fill(color, MOTIF_ALPHA)),
        cv.Oval(x - s * 0.5, y - s * 0.5, s, s * 0.2, paint=_stroke(lighten(color, 0.3), MOTIF_ALPHA + 0.1, 2)),
    ]


_MOTIFS: dict[str, tuple[Callable[[float, float, float, str], list], ...]] = {
    "castle": (_gem, _round_tree, _gem),
    "peaks": (_pine, _pine, _star),
    "valley": (_round_tree, _round_tree, _pine),
    "islands": (_palm, _palm, _star),
    "swamp": (_mushroom, _mushroom, _round_tree),
    "tower": (_book_stack, _pine, _book_stack),
    "observatory": (_star, _planet, _star),
    "meadow": (_round_tree, _pine, _star),
}


def motif_shapes(scene: str, x: float, y: float, size: float, color: str, index: int = 0) -> list:
    motifs = _MOTIFS.get(scene, _MOTIFS["meadow"])
    return motifs[index % len(motifs)](x, y, size, color)


# -- whole scenes ------------------------------------------------------------------------------
def scenery_shapes(
    world_id: str, width: float, height: float, color: str, *,
    motif_count: int = 10, rng: Optional[random.Random] = None,
) -> list:
    """Ground wash + horizon at the top + motifs scattered down both sides
    (never in the middle third, where the road's S-bends cross)."""
    scene = scene_for_world(world_id)
    chooser = rng if rng is not None else random.Random(f"scenery:{world_id}")
    shapes: list = [cv.Rect(0, 0, width, height, paint=_fill(color, GROUND_ALPHA))]
    shapes.extend(horizon_shapes(scene, width, min(HORIZON_HEIGHT, height), color))
    for index in range(motif_count):
        side_left = index % 2 == 0
        x = chooser.uniform(10, width * 0.3) if side_left else chooser.uniform(width * 0.7, width - 10)
        y = chooser.uniform(HORIZON_HEIGHT + 40, max(HORIZON_HEIGHT + 60, height - 20))
        size = chooser.choice((34.0, 44.0, 56.0))
        shapes.extend(motif_shapes(scene, x, y, size, color, index))
    return shapes


def build_scenery(world_id: str, width: float, height: float, color: str, *, rng: Optional[random.Random] = None) -> ft.Container:
    """The drawn backdrop for a map road Stack -- slot it in before the
    road canvas."""
    return ft.Container(
        content=cv.Canvas(shapes=scenery_shapes(world_id, width, height, color, rng=rng)),
        width=width, height=height,
        data={"kind": "scenery", "world": world_id, "scene": scene_for_world(world_id)},
    )


def build_skyline(world_id: str, color: str, *, height: float = SKYLINE_HEIGHT) -> ft.Container:
    """A horizon silhouette along the bottom of a hero header -- positioned
    (left/right/bottom 0) for the header's sky backdrop Stack."""
    scene = scene_for_world(world_id)
    return ft.Container(
        content=cv.Canvas(shapes=horizon_shapes(scene, SKYLINE_VIRTUAL_WIDTH, height, color)),
        left=0, right=0, bottom=0, height=height,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        data={"kind": "skyline", "world": world_id, "scene": scene},
    )
