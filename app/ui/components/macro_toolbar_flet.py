"""A row of quick-insert code-snippet buttons above the editor. Tapping one
stamps a small template into the editor at the current cursor position
(tracked via TextField.on_selection_change, since Flet's TextField only
reports where the caret is through that event -- there's no direct "get
cursor position" call), leaving the caret -- or a text selection, for
fill-in-the-blank snippets like a function name -- in the useful spot.

Flet only: CTk's editor already wraps a raw Tk Text widget with a real
cursor API (insert("insert", text)) and wasn't touched this phase, per the
CTk-parity decision made for phases 7/8.
"""
from __future__ import annotations

from dataclasses import dataclass

import flet as ft


@dataclass(frozen=True)
class Macro:
    label: str
    insert_text: str
    # Offsets into insert_text (not the whole editor value) marking where
    # the caret/selection should land after insertion.
    selection_start: int
    selection_end: int


MACROS: list[Macro] = [
    Macro("print()", "print()", 6, 6),
    Macro("input()", "input()", 6, 6),
    Macro("range()", "range()", 6, 6),
    Macro("if", "if :", 3, 3),
    Macro("for", "for i in range():", 16, 16),
    Macro("while", "while :", 6, 6),
    Macro("def", "def my_function():", 4, 15),
    Macro("#", "# ", 2, 2),
]


@dataclass
class _CursorTracker:
    """Mutable holder so the on_selection_change closure and each macro's
    click handler share the same live cursor position."""
    position: int = 0


def build_macro_toolbar(editor, page: ft.Page, theme) -> ft.Control:
    """`editor` is duck-typed: a plain ft.TextField or anything exposing the
    same .value/.selection/.on_selection_change surface, e.g.
    rich_code_editor_flet.RichCodeEditor."""
    tracker = _CursorTracker(position=len(editor.value or ""))

    def on_selection_change(e: ft.TextSelectionChangeEvent) -> None:
        if e.selection is not None:
            tracker.position = e.selection.start

    editor.on_selection_change = on_selection_change

    def make_handler(macro: Macro):
        def handler(_e: ft.ControlEvent) -> None:
            value = editor.value or ""
            pos = max(0, min(tracker.position, len(value)))
            editor.value = value[:pos] + macro.insert_text + value[pos:]
            new_start = pos + macro.selection_start
            new_end = pos + macro.selection_end
            editor.selection = ft.TextSelection(base_offset=new_start, extent_offset=new_end)
            tracker.position = new_end
            page.update()

        return handler

    buttons = [
        ft.Button(
            macro.label, on_click=make_handler(macro), height=36,
            style=ft.ButtonStyle(bgcolor=theme.bg, color=theme.text),
        )
        for macro in MACROS
    ]
    return ft.Row(buttons, spacing=6, wrap=True)
