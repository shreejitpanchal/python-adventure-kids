"""Pure position math for the Flet Adventure Map (category browser +
level screen, phase 12) -- a winding, node-based path replacing the old
vertical list of full-width cards. Kept dependency-free (no flet import)
so the zigzag math is trivially unit-testable and so both
category_map_flet.py and category_levels_flet.py share one source of
truth instead of duplicating the layout formula.
"""
from __future__ import annotations

from dataclasses import dataclass

NODE_SIZE = 64.0
ROW_HEIGHT = 130.0
PATH_WIDTH = 300.0
LEFT_MARGIN = 20.0
TOP_MARGIN = 20.0
CAPTION_HEIGHT = 46.0


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
    return TOP_MARGIN + (count - 1) * ROW_HEIGHT + NODE_SIZE + CAPTION_HEIGHT
