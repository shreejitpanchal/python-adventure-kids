"""A syntax-highlighted, autocompleting code editor for Flet.

Flet's TextField has no per-token/per-line tagging API (unlike CTk's raw Tk
Text widget, which app/ui/code_editor.py tags directly), so this fakes rich
text by stacking two pixel-aligned layers with identical font/size/padding:
a real ft.TextField on top with its text made transparent (so only the
caret/selection are visible -- the actual text is still there for input,
copy, and accessibility), and underneath it a read-only ft.Text(spans=...)
that's rebuilt from a plain regex tokenizer every keystroke and shows the
colored text the child actually sees. Same TOKEN_PATTERNS/TAG_COLORS as
code_editor.py's CTk tagging, ported here as a pure function since there's
nothing to "tag" in Flet -- just spans to rebuild.

This alignment is best-effort, not pixel-perfect: content_padding is set
to match on both layers, but Flet gives no guarantee the two layout engines
(a Material TextField's internal decoration vs. a plain Text) measure
padding identically across every platform/font. Acceptable for a kids'
code editor; not something to chase further without visual regression
testing infrastructure this repo doesn't have.

Autocomplete suggestions render as a tap-to-insert strip below the editor
(same pattern as macro_toolbar_flet.py) rather than a floating popup
anchored at the caret, because Flet has no API to read a caret's pixel
position -- a floating popup would need fragile per-font position math
that breaks on scroll/wrap.

Exposes the same .value / .selection / .on_selection_change surface as a
plain ft.TextField (what code_editor_flet.py's make_code_editor() returned)
so lesson_screen_flet.py and macro_toolbar_flet.py don't need to know the
editor got smarter -- only the .control accessor (for embedding in the
view) and highlight_error_line()/clear_error_highlight() are new.

Live-typing refreshes (recoloring the underlay, rebuilding the
suggestion strip) are debounced rather than pushed on every keystroke.
Typing fires both on_change and on_selection_change per character, and
each used to call page.update() unconditionally -- two full-page resyncs
per keystroke. On a tablet's software keyboard, which composes whole
words rather than committing one character at a time, that constant
server-driven resync of the live TextField was found to collide with the
keyboard's own composing state: pressing backspace once would delete the
keyboard's entire in-progress composing word instead of one character.
Debouncing collapses a burst of typing into a single page.update() after
a short pause, which is enough to stop stomping on the composing region.
"""
from __future__ import annotations

import asyncio
import keyword
import re

import flet as ft

_REFRESH_DEBOUNCE_SECONDS = 0.2

EDITOR_BGCOLOR = "#1E1E2E"
EDITOR_TEXT_COLOR = "#F1F1F1"
EDITOR_FONT_FAMILY = "Consolas"
ERROR_LINE_BG = "#5A2A2A"

TOKEN_PATTERNS = [
    ("keyword", re.compile(r"\b(" + "|".join(keyword.kwlist) + r")\b")),
    ("builtin", re.compile(r"\b(print|len|range|int|float|str|bool|input|list|dict)\b")),
    ("number", re.compile(r"\b\d+(\.\d+)?\b")),
    ("string", re.compile(r"(\"[^\"\n]*\"|'[^'\n]*')")),
    ("comment", re.compile(r"#.*")),
]

TAG_COLORS = {
    "keyword": "#4F8FF7",
    "builtin": "#A05FD9",
    "number": "#C1791B",
    "string": "#3FA66B",
    "comment": "#9AA0A6",
}

KEYWORDS = set(keyword.kwlist)
BUILTINS = {"print", "len", "range", "int", "float", "str", "bool", "input", "list", "dict"}

_IDENTIFIER = re.compile(r"\b[A-Za-z_]\w*\b")
_WORD_TAIL = re.compile(r"[A-Za-z_]\w*$")


def tokenize(code: str, error_line: int | None = None) -> list[ft.TextSpan]:
    """Splits code into colored TextSpans -- later patterns in
    TOKEN_PATTERNS win over earlier ones for overlapping ranges (so a
    keyword-looking word inside a string renders as a string, matching
    the tag-priority order code_editor.py relies on)."""
    if not code:
        return [ft.TextSpan("")]

    n = len(code)
    colors = [EDITOR_TEXT_COLOR] * n
    for tag, pattern in TOKEN_PATTERNS:
        color = TAG_COLORS[tag]
        for match in pattern.finditer(code):
            for i in range(match.start(), match.end()):
                colors[i] = color

    error_flags = [False] * n
    if error_line:
        start = 0
        for line_number, line in enumerate(code.split("\n"), start=1):
            end = start + len(line)
            if line_number == error_line:
                for i in range(start, end):
                    error_flags[i] = True
                break
            start = end + 1

    spans: list[ft.TextSpan] = []
    run_start = 0
    for i in range(1, n + 1):
        boundary = i == n or colors[i] != colors[run_start] or error_flags[i] != error_flags[run_start]
        if boundary:
            style = ft.TextStyle(
                color=colors[run_start],
                bgcolor=ERROR_LINE_BG if error_flags[run_start] else None,
            )
            spans.append(ft.TextSpan(code[run_start:i], style=style))
            run_start = i
    return spans


def _identifiers_in(code: str) -> set[str]:
    return set(_IDENTIFIER.findall(code)) - KEYWORDS


def _word_at_cursor(value: str, pos: int) -> tuple[str, int, int]:
    """The identifier prefix immediately before the cursor, and its
    [start, end) range in value -- end is always the cursor position
    itself, since autocomplete only replaces what's already typed, not
    anything after the caret."""
    pos = max(0, min(pos, len(value)))
    match = _WORD_TAIL.search(value[:pos])
    if not match:
        return "", pos, pos
    return match.group(0), match.start(), pos


class RichCodeEditor:
    def __init__(self, page: ft.Page, theme, initial_code: str = "", height: int = 220) -> None:
        self._page = page
        self._theme = theme
        self._cursor_pos = len(initial_code)
        self._error_line: int | None = None
        self._external_selection_handler = None
        self._refresh_timer: asyncio.TimerHandle | None = None

        self._underlay = ft.Text(
            spans=tokenize(initial_code),
            style=ft.TextStyle(font_family=EDITOR_FONT_FAMILY, size=15),
        )
        underlay_container = ft.Container(
            content=self._underlay, bgcolor=EDITOR_BGCOLOR, border_radius=4,
            padding=ft.padding.Padding.all(12), expand=True,
        )

        self._field = ft.TextField(
            value=initial_code,
            multiline=True,
            min_lines=6,
            max_lines=20,
            text_style=ft.TextStyle(font_family=EDITOR_FONT_FAMILY, size=15, color="transparent"),
            cursor_color=EDITOR_TEXT_COLOR,
            bgcolor="transparent",
            border_color="#3A3A4E",
            content_padding=ft.padding.Padding.all(12),
            expand=True,
            on_change=self._on_field_change,
            on_selection_change=self._on_field_selection_change,
        )

        self._suggestion_row = ft.Row([], spacing=6, wrap=True)

        self.control = ft.Column(
            [ft.Stack([underlay_container, self._field], height=height), self._suggestion_row],
            spacing=6,
        )

    # -- surface expected by lesson_screen_flet.py / macro_toolbar_flet.py --
    @property
    def value(self) -> str:
        return self._field.value or ""

    @value.setter
    def value(self, code: str) -> None:
        if self._refresh_timer is not None:
            self._refresh_timer.cancel()
            self._refresh_timer = None
        self._field.value = code
        self._cursor_pos = len(code or "")
        self._refresh_underlay()
        self._rebuild_suggestions()

    @property
    def selection(self):
        return self._field.selection

    @selection.setter
    def selection(self, value) -> None:
        self._field.selection = value

    @property
    def on_selection_change(self):
        return self._external_selection_handler

    @on_selection_change.setter
    def on_selection_change(self, handler) -> None:
        # Stored and chained rather than replacing self._field's own
        # handler, since this editor's own cursor tracking (for
        # autocomplete) also needs every selection-change event -- both
        # this class and callers like build_macro_toolbar() observe the
        # same stream instead of fighting over one assignment slot.
        self._external_selection_handler = handler

    # -- error line highlight (mirrors code_editor.py's CTk API) --------------
    def highlight_error_line(self, line_number: int) -> None:
        self._error_line = line_number
        self._refresh_underlay()

    def clear_error_highlight(self) -> None:
        self._error_line = None
        self._refresh_underlay()

    # -- internals --------------------------------------------------------------
    def _on_field_change(self, e: ft.ControlEvent) -> None:
        self._schedule_refresh()

    def _on_field_selection_change(self, e: ft.TextSelectionChangeEvent) -> None:
        if e.selection is not None:
            self._cursor_pos = e.selection.start
        # The external handler (e.g. build_macro_toolbar()'s cursor
        # tracker) only touches plain Python state, not a UI control, so
        # it's called immediately rather than deferred with the rest --
        # it needs to always reflect the real cursor position by the time
        # a macro button is tapped, not lag behind a debounce window.
        if self._external_selection_handler is not None:
            self._external_selection_handler(e)
        self._schedule_refresh()

    def _schedule_refresh(self) -> None:
        """Coalesces the underlay/suggestion rebuild (and the page.update()
        that pushes it to the client) into one call after a short pause in
        typing, instead of one-or-two per keystroke -- see the module
        docstring for why that matters on tablet software keyboards."""
        if self._refresh_timer is not None:
            self._refresh_timer.cancel()
        loop = asyncio.get_running_loop()
        self._refresh_timer = loop.call_later(_REFRESH_DEBOUNCE_SECONDS, self._do_refresh)

    def _do_refresh(self) -> None:
        self._refresh_timer = None
        self._refresh_underlay()
        self._rebuild_suggestions()
        self._page.update()

    def _refresh_underlay(self) -> None:
        self._underlay.spans = tokenize(self._field.value or "", self._error_line)

    def _rebuild_suggestions(self) -> None:
        value = self._field.value or ""
        word, start, end = _word_at_cursor(value, self._cursor_pos)
        if not word:
            self._suggestion_row.controls = []
            return

        candidates = KEYWORDS | BUILTINS | _identifiers_in(value)
        matches = sorted(c for c in candidates if c != word and c.startswith(word))[:6]
        self._suggestion_row.controls = [
            ft.Button(
                match, on_click=self._make_suggestion_handler(match, start, end), height=32,
                style=ft.ButtonStyle(bgcolor=self._theme.bg, color=self._theme.text),
            )
            for match in matches
        ]

    def _make_suggestion_handler(self, word: str, start: int, end: int):
        def handler(_e: ft.ControlEvent) -> None:
            value = self._field.value or ""
            new_value = value[:start] + word + value[end:]
            self._field.value = new_value
            cursor = start + len(word)
            self._field.selection = ft.TextSelection(base_offset=cursor, extent_offset=cursor)
            self._cursor_pos = cursor
            self._refresh_underlay()
            self._rebuild_suggestions()
            self._page.update()

        return handler
