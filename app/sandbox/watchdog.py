"""Cooperative timeout mechanism for the in-process sandbox runner.

Unlike the subprocess-based runner (app/sandbox/runner.py), code executed
by app/sandbox/inprocess_runner.py runs inside this same process -- that's
required on Android, which won't let a non-rooted app spawn a sibling OS
process the way Windows' subprocess.Popen does. With no OS-level kill
switch available for a runaway loop, an AST transform below inserts a call
to a watchdog's tick() at the top of every for/while loop body. tick() is
cheap on its own and only checks the wall clock every CHECK_INTERVAL
calls, so it stays negligible even inside a tight, multi-million-iteration
loop -- but the cancellation flag is checked on every single call, so a
user-requested Stop is still picked up promptly.

Known, accepted limitation: a single expensive operation with no loop or
function call at all (e.g. 10**10**10**10) can't be interrupted by any
pure-Python cooperative mechanism, including this one. Acceptable for
curated lesson content; not solved here.
"""
from __future__ import annotations

import ast
import threading
import time

CHECK_INTERVAL = 200
TICK_FUNC_NAME = "__pyadv_tick__"


class WatchdogTimeout(BaseException):
    """Raised inside child code when it runs past its deadline or is
    cancelled. Subclasses BaseException (not Exception) so a bare
    `except Exception` -- or a swallow-everything `except: pass` a curious
    kid might write -- can't accidentally catch and ignore it."""


class Watchdog:
    def __init__(self, timeout: float) -> None:
        self._deadline = time.monotonic() + timeout
        self._cancelled = threading.Event()
        self._count = 0

    def cancel(self) -> None:
        self._cancelled.set()

    def tick(self) -> None:
        if self._cancelled.is_set():
            raise WatchdogTimeout()
        self._count += 1
        if self._count % CHECK_INTERVAL == 0 and time.monotonic() >= self._deadline:
            raise WatchdogTimeout()


class _LoopTickInjector(ast.NodeTransformer):
    """Inserts a call to __pyadv_tick__() as the first statement in every
    for/while loop body. Runs on a fresh parse of source that has already
    passed check_code_safety() -- this transform doesn't re-validate
    anything, it only adds ticks, so it must never run on unchecked source.

    The injected call reuses the loop statement's own line number (via
    ast.copy_location) rather than introducing a new one, so line numbers
    reported in tracebacks for the rest of the child's code stay accurate.
    """

    def visit_For(self, node: ast.For) -> ast.For:
        self.generic_visit(node)
        node.body.insert(0, self._tick_statement(node))
        return node

    def visit_While(self, node: ast.While) -> ast.While:
        self.generic_visit(node)
        node.body.insert(0, self._tick_statement(node))
        return node

    @staticmethod
    def _tick_statement(node: ast.AST) -> ast.Expr:
        tick = ast.Expr(
            value=ast.Call(func=ast.Name(id=TICK_FUNC_NAME, ctx=ast.Load()), args=[], keywords=[])
        )
        ast.copy_location(tick, node)
        ast.fix_missing_locations(tick)
        return tick


def compile_with_watchdog(source: str, filename: str = "<your code>"):
    """Parses source, injects watchdog ticks into every loop, and compiles
    the result. Caller must have already run check_code_safety() on the
    ORIGINAL source -- this transform trusts that and doesn't re-check
    anything itself."""
    tree = ast.parse(source, filename=filename)
    tree = _LoopTickInjector().visit(tree)
    ast.fix_missing_locations(tree)
    return compile(tree, filename=filename, mode="exec", optimize=0)
