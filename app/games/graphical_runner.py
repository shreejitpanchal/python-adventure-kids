"""Runs a graphical lesson's code in-process against a live GameCanvas.

Unlike app/sandbox/runner.py, this cannot use OS-process isolation --
Tkinter widgets must be created and touched from the main thread, and a
long-running game needs to keep interacting with the same canvas over
time. The same AST safety check and restricted builtins apply as defense
in depth, plus a while-loop ban (see app/sandbox/safety.py) since there's
no OS timeout here to save us from a runaway loop.
"""
from __future__ import annotations

import builtins
import traceback
from dataclasses import dataclass

from app.games.game_canvas import GameCanvas
from app.sandbox.allowed_builtins import ALLOWED_BUILTIN_NAMES
from app.sandbox.safety import ALLOWED_MODULES, SafetyViolation, check_code_safety


@dataclass
class GraphicalExecutionResult:
    success: bool
    blocked: bool = False
    blocked_message: str = ""
    traceback_text: str = ""


def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    root_module = name.split(".")[0]
    if root_module not in ALLOWED_MODULES:
        raise ImportError(f"Importing '{name}' is not allowed here yet.")
    return builtins.__import__(name, globals, locals, fromlist, level)


def run_graphical_code(code: str, game_canvas: GameCanvas) -> GraphicalExecutionResult:
    try:
        check_code_safety(code, disallow_while=True)
    except SafetyViolation as violation:
        return GraphicalExecutionResult(success=False, blocked=True, blocked_message=violation.message)

    safe_builtins = {
        name: getattr(builtins, name) for name in ALLOWED_BUILTIN_NAMES if hasattr(builtins, name)
    }
    safe_builtins["__import__"] = _restricted_import
    restricted_globals = {"__builtins__": safe_builtins, "game": game_canvas}

    try:
        compiled = compile(code, "<your code>", "exec")
        exec(compiled, restricted_globals)
    except Exception:
        return GraphicalExecutionResult(success=False, traceback_text=traceback.format_exc())

    return GraphicalExecutionResult(success=True)
