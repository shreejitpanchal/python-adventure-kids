"""Translates raw Python tracebacks into kid-friendly messages. Raw text stays available on request."""
from __future__ import annotations

import re
from typing import Optional

FRIENDLY: dict[str, tuple[str, str]] = {
    "SyntaxError": (
        "🧩 Something isn't quite right with how the code is written.",
        "Check for missing parentheses, quotes, or colons.",
    ),
    "IndentationError": (
        "📏 The spacing at the start of a line doesn't match up.",
        "Python cares about spaces — try lining things up with the line above.",
    ),
    "TabError": (
        "📏 The spacing at the start of a line doesn't match up.",
        "Try using spaces consistently instead of mixing tabs and spaces.",
    ),
    "NameError": (
        "🤔 Python doesn't recognize one of the words you used.",
        "Check the spelling, or make sure you created it before using it.",
    ),
    "TypeError": (
        "🔧 Python got a kind of value it didn't expect.",
        "Double check you're combining the right kinds of things, like numbers with numbers.",
    ),
    "ZeroDivisionError": (
        "➗ You can't divide by zero!",
        "Try dividing by a different number.",
    ),
    "ImportError": (
        "📦 That's not available in this lesson yet.",
        "Try solving it with what you've learned so far.",
    ),
    "ModuleNotFoundError": (
        "📦 That's not available in this lesson yet.",
        "Try solving it with what you've learned so far.",
    ),
    "IndexError": (
        "🔎 Python tried to find something that isn't there.",
        "Check that you're not looking past the end of a list.",
    ),
    "KeyError": (
        "🔎 Python couldn't find that name in there.",
        "Double check the spelling matches exactly.",
    ),
    "ValueError": (
        "🔧 Python got a value that didn't make sense here.",
        "Double check the value you're using matches what's expected.",
    ),
    "EOFError": (
        "🧑 Python was waiting for an answer that didn't come.",
        "Make sure you've typed something in the answer box, then press RUN again.",
    ),
}

DEFAULT_MESSAGE = "😅 Something went wrong while running your code."
DEFAULT_HINT = "Take a look at your code and try again."

_CODE_FRAME_RE = re.compile(r'File "<your code>", line (\d+)')


def translate_error(stderr: str) -> tuple[str, str]:
    exc_type = _last_exception_type(stderr)
    return FRIENDLY.get(exc_type, (DEFAULT_MESSAGE, DEFAULT_HINT))


def _last_exception_type(stderr: str) -> str:
    for line in reversed(stderr.strip().splitlines()):
        line = line.strip()
        if line:
            return line.split(":", 1)[0].strip()
    return ""


def extract_error_line_number(stderr: str) -> Optional[int]:
    matches = _CODE_FRAME_RE.findall(stderr)
    return int(matches[-1]) if matches else None
