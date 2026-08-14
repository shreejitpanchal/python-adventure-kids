"""Executes a child's Python code safely, in-process.

Replaces the subprocess-based runner.py/worker.py -- Android's app
sandboxing won't let a non-rooted app spawn a sibling OS process the way
Windows' subprocess.Popen does, so this runs identically on both
platforms: a static AST check, then exec() against a restricted builtins
set, with a cooperative watchdog (app/sandbox/watchdog.py) standing in for
the OS-level kill that used to handle infinite loops.

Also serves graphical lessons (Snake) via the optional `game` parameter,
injected into the exec globals -- this folds what used to be a separate
app/games/graphical_runner.py into the same engine, so there's exactly one
execution path instead of two that could drift apart. Graphical lessons
pass disallow_while=True for the same reason they always have: animation
must use game.after(...) callbacks that yield control, not a blocking
loop.

This function is synchronous and blocking, like the runner it replaces --
a caller that must keep a UI thread responsive (as the lesson screen does)
is expected to invoke it from its own background thread, exactly as
before.
"""
from __future__ import annotations

import builtins
import contextlib
import io
import threading
import traceback
from dataclasses import dataclass
from typing import Any, Optional

from app.sandbox.allowed_builtins import ALLOWED_BUILTIN_NAMES
from app.sandbox.safety import ALLOWED_MODULES, SafetyViolation, check_code_safety
from app.sandbox.watchdog import TICK_FUNC_NAME, Watchdog, WatchdogTimeout, compile_with_watchdog

DEFAULT_TIMEOUT_SECONDS = 5.0
CODE_FILENAME = "<your code>"

# contextlib.redirect_stdout mutates process-global state (sys.stdout), so
# only one sandboxed run can be in flight at a time -- enforced here as a
# defensive invariant, not just trusted to callers.
_run_lock = threading.Lock()


@dataclass
class ExecutionResult:
    success: bool
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    blocked: bool = False
    blocked_message: str = ""


class RunHandle:
    """Lets the UI cancel a run that's in progress (e.g. an infinite loop).

    Python threads can't be forcibly killed, so cancellation is
    cooperative: it sets a flag the watchdog checks on every tick (see
    Watchdog.tick), which for any loop is at most one iteration away.
    """

    def __init__(self) -> None:
        self._watchdog: Optional[Watchdog] = None
        self._lock = threading.Lock()
        self.cancelled = False

    def _attach(self, watchdog: Watchdog) -> None:
        with self._lock:
            self._watchdog = watchdog
            if self.cancelled:
                watchdog.cancel()

    def cancel(self) -> None:
        with self._lock:
            self.cancelled = True
            if self._watchdog is not None:
                self._watchdog.cancel()


def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    root_module = name.split(".")[0]
    if root_module not in ALLOWED_MODULES:
        raise ImportError(f"Importing '{name}' is not allowed here yet.")
    return builtins.__import__(name, globals, locals, fromlist, level)


def _make_input(answers: list[str], out: io.StringIO):
    def _input(prompt: str = "") -> str:
        if prompt:
            out.write(str(prompt))
        if not answers:
            raise EOFError()
        return answers.pop(0)

    return _input


def _split_stdin(stdin_text: Optional[str]) -> list[str]:
    """Mirrors how a real stdin pipe behaves: a trailing newline marks the
    end of the last line, it doesn't introduce a phantom empty one after
    it. "Sam\\n" -> one answer ("Sam"), not two."""
    answers = (stdin_text or "").split("\n")
    if answers and answers[-1] == "":
        answers.pop()
    return answers


def _build_globals(
    watchdog: Watchdog, out: io.StringIO, stdin_text: Optional[str], game: Optional[Any]
) -> dict:
    safe_builtins = {
        name: getattr(builtins, name) for name in ALLOWED_BUILTIN_NAMES if hasattr(builtins, name)
    }
    safe_builtins["__import__"] = _restricted_import
    safe_builtins["input"] = _make_input(_split_stdin(stdin_text), out)

    exec_globals: dict = {"__builtins__": safe_builtins, TICK_FUNC_NAME: watchdog.tick}
    if game is not None:
        exec_globals["game"] = game
    return exec_globals


def run_code(
    code: str,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    handle: Optional[RunHandle] = None,
    stdin_text: Optional[str] = None,
    *,
    game: Optional[Any] = None,
    disallow_while: bool = False,
) -> ExecutionResult:
    try:
        check_code_safety(code, disallow_while=disallow_while)
    except SafetyViolation as violation:
        return ExecutionResult(success=False, blocked=True, blocked_message=violation.message)

    with _run_lock:
        watchdog = Watchdog(timeout)
        if handle is not None:
            handle._attach(watchdog)

        out = io.StringIO()
        exec_globals = _build_globals(watchdog, out, stdin_text, game)

        try:
            with contextlib.redirect_stdout(out):
                compiled = compile_with_watchdog(code, filename=CODE_FILENAME)
                exec(compiled, exec_globals)
        except WatchdogTimeout:
            return ExecutionResult(success=False, timed_out=True, stdout=out.getvalue())
        except Exception:
            return ExecutionResult(success=False, stdout=out.getvalue(), stderr=traceback.format_exc())

    return ExecutionResult(success=True, stdout=out.getvalue())
