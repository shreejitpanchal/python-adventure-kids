"""A child-friendly code editor -- Phase 5 MVP.

A plain monospace multiline TextField, no live syntax highlighting or
per-line error highlighting. The old CTk editor (app/ui/code_editor.py)
got both by tagging a raw Tk Text widget directly; Flet's TextField has no
equivalent per-token/per-line tagging API, and building a custom
rich-text/canvas-based editor to get it back is explicitly a stretch goal
for later, not a blocker, per the re-platform plan. The error line number
(when available) is still surfaced to the child in the output text itself
-- see app/ui/lesson_screen_flet.py -- just not highlighted inline.
"""
from __future__ import annotations

import flet as ft

EDITOR_BGCOLOR = "#1E1E2E"
EDITOR_TEXT_COLOR = "#F1F1F1"
EDITOR_FONT_FAMILY = "Consolas"


def make_code_editor(initial_code: str = "", height: int = 220, scale: float = 1.0) -> ft.TextField:
    return ft.TextField(
        value=initial_code,
        multiline=True,
        min_lines=6,
        max_lines=20,
        height=height,
        text_style=ft.TextStyle(
            font_family=EDITOR_FONT_FAMILY, size=max(1, round(15 * scale)), color=EDITOR_TEXT_COLOR,
        ),
        bgcolor=EDITOR_BGCOLOR,
        border_color="#3A3A4E",
    )


def make_read_only_code_block(code: str, scale: float = 1.0) -> ft.Control:
    """A non-editable, monospace code block for showing examples."""
    return ft.Container(
        content=ft.Text(
            code, font_family=EDITOR_FONT_FAMILY, size=max(1, round(15 * scale)),
            color=EDITOR_TEXT_COLOR, selectable=True,
        ),
        bgcolor=EDITOR_BGCOLOR, border_radius=8, padding=14,
    )
