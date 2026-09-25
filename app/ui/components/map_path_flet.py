"""Shared pieces of the Flet Adventure Map: the winding road drawn between
nodes, the chunky 3D node discs, and the "you are here" Codey marker --
used by both category_map_flet.py (one node per category) and
category_levels_flet.py (one node per level) so the two maps look like
the same world. Geometry comes from app/ui/adventure_map_layout.py; this
module only turns positions into controls. Flet only.
"""
from __future__ import annotations

from typing import Callable, Optional, Sequence

import flet as ft
import flet.canvas as cv

from app.ui.adventure_map_layout import MARKER_SIZE, NODE_LIP, NODE_SIZE, NodePosition, curve_control_points, marker_position
from app.ui.color_utils import contrasting_text_color, darken, lighten, with_alpha
from app.ui.components import motion_flet as motion
from app.ui.components.adventure_kit_flet import accent_gradient, lip_shadow, soft_shadow
from app.ui.theme_flet import ThemePreset, scaled

ROAD_OUTER_WIDTH = 16
ROAD_INNER_WIDTH = 9


def _bezier(a: NodePosition, b: NodePosition) -> list:
    cp1x, cp1y, cp2x, cp2y = curve_control_points(a, b)
    return [
        cv.Path.MoveTo(a.center_x, a.center_y),
        cv.Path.CubicTo(cp1x, cp1y, cp2x, cp2y, b.center_x, b.center_y),
    ]


def road_shapes(positions: Sequence[NodePosition], segment_done: Sequence[bool], theme: ThemePreset) -> list:
    """Canvas shapes for the road: each segment is an S-bend drawn as a
    darker wide stroke with a lighter stroke on top (a curb and a road).
    Segments whose both endpoints are complete turn the success color, so
    the child can see how far the path has been paved."""
    shapes: list = []
    for i in range(len(positions) - 1):
        base = theme.success if segment_done[i] else theme.text_muted
        shapes.append(cv.Path(
            _bezier(positions[i], positions[i + 1]),
            paint=ft.Paint(color=darken(base, 0.3), stroke_width=ROAD_OUTER_WIDTH, style=ft.PaintingStyle.STROKE),
        ))
        shapes.append(cv.Path(
            _bezier(positions[i], positions[i + 1]),
            paint=ft.Paint(color=lighten(base, 0.2), stroke_width=ROAD_INNER_WIDTH, style=ft.PaintingStyle.STROKE),
        ))
    return shapes


def build_map_node(
    *, position: NodePosition, face: str, color: str, scale: float,
    on_click: Optional[Callable] = None, data: Optional[dict] = None,
    dim: bool = False, face_size: int = 28, highlight: bool = False,
) -> ft.Container:
    """A chunky disc on the path. `dim` renders a flat, lip-less locked
    look; `highlight` adds a bright rim for the node the child should tap
    next. Positioned with left/top for the parent Stack."""
    text_color = contrasting_text_color(color)
    disc = ft.Container(
        content=ft.Text(face, size=scaled(face_size, scale), weight=ft.FontWeight.BOLD, color=text_color, text_align=ft.TextAlign.CENTER),
        width=NODE_SIZE, height=NODE_SIZE, border_radius=NODE_SIZE / 2,
        gradient=None if dim else accent_gradient(color),
        bgcolor=color if dim else None,
        shadow=None if dim else lip_shadow(color, depth=NODE_LIP),
        border=ft.border.Border.all(4, with_alpha("#FFFFFF", 0.9)) if highlight else None,
        alignment=ft.alignment.Alignment.CENTER,
    )
    motion.prepare_pulse(disc)
    node = ft.Container(
        content=disc,
        left=position.x, top=position.y, width=NODE_SIZE, height=NODE_SIZE + NODE_LIP,
        on_click=on_click, ink=on_click is not None,
        data=data,
    )
    return node


def node_disc(node: ft.Container) -> ft.Container:
    return node.content


def build_you_are_here(position: NodePosition, theme: ThemePreset, scale: float, *, page=None) -> ft.Container:
    """Codey hovering above the node to play next, floating up and down."""
    left, top = marker_position(position)
    marker = ft.Container(
        content=ft.Text("🤖", size=scaled(22, scale), text_align=ft.TextAlign.CENTER),
        width=MARKER_SIZE, height=MARKER_SIZE, border_radius=MARKER_SIZE / 2,
        bgcolor=theme.card, shadow=soft_shadow(opacity=0.2, blur=10, dy=4),
        alignment=ft.alignment.Alignment.CENTER,
        left=left, top=top,
        data={"kind": "you_are_here"},
    )
    motion.prepare_bob(marker)
    if page is not None:
        motion.bob(page, marker, times=6, dy=0.15)
    return marker
