"""A child-friendly code editor: CTkTextbox + syntax highlighting, auto-indent, undo/redo, error line highlight."""
from __future__ import annotations

import keyword
import re

import customtkinter as ctk

from app.ui import theme

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


def configure_highlight_tags(raw_text_widget) -> None:
    for tag, color in TAG_COLORS.items():
        raw_text_widget.tag_configure(tag, foreground=color)


def apply_highlighting(raw_text_widget) -> None:
    content = raw_text_widget.get("1.0", "end-1c")
    for tag in TAG_COLORS:
        raw_text_widget.tag_remove(tag, "1.0", "end")
    for tag, pattern in TOKEN_PATTERNS:
        for match in pattern.finditer(content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            raw_text_widget.tag_add(tag, start, end)


def make_read_only_code_block(master, code: str, height: int = 80) -> ctk.CTkTextbox:
    """A non-editable, syntax-highlighted code block for showing examples."""
    box = ctk.CTkTextbox(
        master,
        height=height,
        font=theme.font_mono(15),
        fg_color="#1E1E2E",
        text_color="#F1F1F1",
        wrap="none",
    )
    raw = box._textbox
    configure_highlight_tags(raw)
    box.insert("1.0", code)
    apply_highlighting(raw)
    box.configure(state="disabled")
    return box


class CodeEditor(ctk.CTkFrame):
    def __init__(self, master, height: int = 180) -> None:
        super().__init__(master, fg_color="transparent")

        self.textbox = ctk.CTkTextbox(
            self,
            height=height,
            font=theme.font_mono(16),
            fg_color="#1E1E2E",
            text_color="#F1F1F1",
            wrap="none",
        )
        self.textbox.pack(fill="both", expand=True)

        self._raw = self.textbox._textbox
        self._raw.configure(undo=True, autoseparators=True, maxundo=-1)

        configure_highlight_tags(self._raw)
        self._raw.tag_configure("error_line", background="#5A2A2A")

        self._raw.bind("<KeyRelease>", self._on_key_release)
        self._raw.bind("<Return>", self._on_return)
        self._raw.bind("<Control-z>", lambda e: self._undo())
        self._raw.bind("<Control-y>", lambda e: self._redo())
        self._raw.bind("<Control-Shift-Z>", lambda e: self._redo())

    # -- content -----------------------------------------------------------
    def get_code(self) -> str:
        return self.textbox.get("1.0", "end-1c")

    def set_code(self, code: str) -> None:
        self._raw.edit_reset()
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", code)
        self._highlight()

    def focus_editor(self) -> None:
        self._raw.focus_set()

    def set_enabled(self, enabled: bool) -> None:
        self.textbox.configure(state="normal" if enabled else "disabled")

    # -- error line highlight ------------------------------------------------
    def highlight_error_line(self, line_number: int) -> None:
        self._raw.tag_remove("error_line", "1.0", "end")
        self._raw.tag_add("error_line", f"{line_number}.0", f"{line_number}.0 lineend+1c")

    def clear_error_highlight(self) -> None:
        self._raw.tag_remove("error_line", "1.0", "end")

    # -- internals -----------------------------------------------------------
    def _on_key_release(self, event) -> None:
        if event.keysym in ("Control_L", "Control_R", "Shift_L", "Shift_R"):
            return
        self.clear_error_highlight()
        self._highlight()

    def _on_return(self, event):
        widget = event.widget
        line = widget.get("insert linestart", "insert")
        stripped = line.rstrip()
        indent = re.match(r"[ \t]*", line).group(0)
        if stripped.endswith(":"):
            indent += "    "
        widget.insert("insert", "\n" + indent)
        self._highlight()
        return "break"

    def _undo(self):
        try:
            self._raw.edit_undo()
        except Exception:
            pass
        self._highlight()
        return "break"

    def _redo(self):
        try:
            self._raw.edit_redo()
        except Exception:
            pass
        self._highlight()
        return "break"

    def _highlight(self) -> None:
        apply_highlighting(self._raw)
