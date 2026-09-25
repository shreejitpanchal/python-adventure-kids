"""Pure position math for the Flet Adventure Map (category browser +
level screen) -- a winding, node-based path replacing the old vertical
list of full-width cards. Kept dependency-free (no flet import) so the
zigzag and curve math is trivially unit-testable and so both
category_map_flet.py and category_levels_flet.py share one source of
truth instead of duplicating the layout formula.
"""
from __future__ import annotations

from dataclasses import dataclass

NODE_SIZE = 72.0
# Extra height under each node for its chunky 3D "base" (the darker disc
# offset a few pixels below the face) -- see adventure_kit_flet.py.
NODE_LIP = 6.0
ROW_HEIGHT = 144.0
PATH_WIDTH = 300.0
LEFT_MARGIN = 20.0
# Room above the first node for the "you are here" Codey marker.
TOP_MARGIN = 44.0
CAPTION_HEIGHT = 50.0
MARKER_SIZE = 40.0


@dataclass(frozen=True)
class NodePosition:
    x: float
    y: float

    @property
    def center_x(self) -> float:
        return self.x + NODE_SIZE / 2

    @property
    def center_y(self) -> float:
        return self.y + NODE_SIZE / 2


def zigzag_positions(count: int) -> list[NodePosition]:
    """One position per node, alternating left/right down the screen --
    the S-curve a physical board-game path winds along. Node 0 starts on
    the left; each subsequent node alternates sides and drops one row."""
    right_x = PATH_WIDTH - NODE_SIZE - LEFT_MARGIN
    positions = []
    for i in range(count):
        x = LEFT_MARGIN if i % 2 == 0 else right_x
        y = TOP_MARGIN + i * ROW_HEIGHT
        positions.append(NodePosition(x=x, y=y))
    return positions


def total_path_height(count: int) -> float:
    """Stack/Canvas height needed to fit every node plus its caption."""
    if count == 0:
        return TOP_MARGIN
    return TOP_MARGIN + (count - 1) * ROW_HEIGHT + NODE_SIZE + NODE_LIP + CAPTION_HEIGHT


def curve_control_points(start: NodePosition, end: NodePosition) -> tuple[float, float, float, float]:
    """(cp1_x, cp1_y, cp2_x, cp2_y) for a cubic Bezier from start's center
    to end's center that leaves the first node straight down and arrives at
    the second straight down -- a smooth S-bend road between two zigzag
    nodes instead of a straight diagonal line. Both control points sit at
    the vertical midpoint, each directly below/above its own node."""
    mid_y = (start.center_y + end.center_y) / 2
    return start.center_x, mid_y, end.center_x, mid_y


def marker_position(node: NodePosition) -> tuple[float, float]:
    """(left, top) of the "you are here" marker centered above a node."""
    return node.center_x - MARKER_SIZE / 2, node.y - MARKER_SIZE + 6
