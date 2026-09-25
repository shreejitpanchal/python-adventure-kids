"""Compatibility wrapper only -- scheduled for deletion.

The graphical execution path now lives in app/sandbox/inprocess_runner.py:
`run_code(code, game=game_canvas, disallow_while=True)`, the same engine
the Flet app uses for everything, so there is exactly one sandbox
implementation instead of a hand-copied second one here. Both UIs' lesson
screens already call that directly (app/ui/lesson_screen.py,
app/ui/lesson_screen_flet.py).

This module only adapts that engine's ExecutionResult to the older
GraphicalExecutionResult shape for the one remaining caller,
tests/test_graphical_runner.py. Delete both files together; new code must
not import this module.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.sandbox.inprocess_runner import run_code


@dataclass
class GraphicalExecutionResult:
    success: bool
    blocked: bool = False
    blocked_message: str = ""
    traceback_text: str = ""


def run_graphical_code(code: str, game_canvas) -> GraphicalExecutionResult:
    result = run_code(code, game=game_canvas, disallow_while=True)
    return GraphicalExecutionResult(
        success=result.success,
        blocked=result.blocked,
        blocked_message=result.blocked_message,
        traceback_text=result.stderr,
    )
