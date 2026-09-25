"""Static (AST-based) safety check, run before any child code is executed.

This is the first of two layers. Every execution engine also runs the code
against the restricted runtime environment built by
app/sandbox/allowed_builtins.py (restricted builtins, restricted import
that serves public-only views of allowlisted modules) as defense in depth.
The two layers cover different ground: this one rejects *spellings* that
could reach interpreter internals -- dunder names, frame/generator
introspection attributes, leading-underscore attributes -- while the
runtime layer makes sure the dangerous objects simply aren't there for a
spelling this check didn't anticipate.
"""
from __future__ import annotations

import ast
from typing import Optional

BLOCKED_NAMES = {
    "eval", "exec", "compile", "__import__", "open",
    "globals", "locals", "vars", "dir",
    "getattr", "setattr", "delattr",
    "breakpoint", "exit", "quit", "help", "memoryview",
}

# A short, deliberate allowlist -- extended as lessons need more of the
# standard library. Everything else stays blocked. This is the single
# source of truth: app/sandbox/allowed_builtins.py's restricted __import__
# reads it too, so there is nothing else to keep in sync.
# time/collections/itertools/datetime/json/functools were added for the
# Python Learning course's "Standard Library Deep Dive" and "Advanced
# Programming Concepts" chapters -- all pure-computation or clock-reading
# modules, no filesystem/network/process access, so they don't weaken the
# sandbox's isolation guarantees. threading/asyncio/logging were
# deliberately left out: real concurrency doesn't compose safely with
# this sandbox's "hard-kill the process after 5s" timeout model (a
# thread or event loop can outlive that kill in ways a straight-line
# script can't) -- the course's concurrency-related lessons teach the
# concepts without importing those modules for real.
ALLOWED_MODULES = {"random", "time", "collections", "itertools", "datetime", "json", "functools"}

# Attributes that walk from an object the child legitimately holds (a
# generator, an exception) out to interpreter internals. A generator's
# gi_frame -> f_back is the frame that called exec(), and that frame's
# f_globals is the runner's own module namespace -- the real `builtins`
# module, `open` and all. None of these names are dunders, so the dunder
# rule below doesn't catch them on its own.
BLOCKED_ATTRIBUTES = {
    "gi_frame", "gi_code", "gi_yieldfrom",
    "cr_frame", "cr_code", "cr_await", "cr_origin",
    "ag_frame", "ag_code", "ag_await",
    "f_back", "f_globals", "f_builtins", "f_locals", "f_code", "f_trace",
    "tb_frame", "tb_next",
}

# Leading-underscore attributes are private and blocked wholesale --
# random._os *is* the os module and collections._sys is sys -- with one
# exception: namedtuple's public API is spelled with a leading underscore
# by design, and course content teaches it.
ALLOWED_PRIVATE_ATTRIBUTES = {"_replace", "_asdict", "_fields", "_make", "_field_defaults"}

INTERNAL_NAME_MESSAGE = "Using names like this isn't allowed."
PRIVATE_NAME_MESSAGE = "Names that start with an underscore are private -- this lesson can't use them."


class SafetyViolation(Exception):
    def __init__(self, message: str, line: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.line = line


def _is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


class _SafetyVisitor(ast.NodeVisitor):
    """Rejects dunder identifiers everywhere they could be *bound* -- plain
    names, parameters, import aliases, global/nonlocal declarations, except
    handler targets, match captures -- not just where they're read. The
    in-process watchdog (app/sandbox/watchdog.py) injects a call to a
    dunder-named tick function into every loop; if child code could bind
    that name, it could shadow the tick with a no-op and disable the
    timeout. The one place a dunder def is legitimate is a method directly
    inside a class body (__init__, __str__, ...), which binds a class
    attribute rather than anything the injected call could resolve to.
    """

    def __init__(self, disallow_while: bool = False):
        self.disallow_while = disallow_while
        self._class_body_methods: set[int] = set()

    def _check_identifier(self, name: Optional[str], node: ast.AST) -> None:
        if name is not None and _is_dunder(name):
            raise SafetyViolation(INTERNAL_NAME_MESSAGE, getattr(node, "lineno", None))

    # -- imports ---------------------------------------------------------------
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root_module = alias.name.split(".")[0]
            if root_module not in ALLOWED_MODULES:
                raise SafetyViolation(
                    f"Importing '{alias.name}' isn't allowed in lessons yet.", node.lineno
                )
            self._check_identifier(alias.asname, node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        root_module = (node.module or "").split(".")[0]
        if root_module not in ALLOWED_MODULES:
            raise SafetyViolation(
                f"Importing from '{node.module}' isn't allowed in lessons yet.", node.lineno
            )
        for alias in node.names:
            if alias.name.startswith("_"):
                raise SafetyViolation(PRIVATE_NAME_MESSAGE, node.lineno)
            self._check_identifier(alias.asname, node)
        self.generic_visit(node)

    # -- names and attributes ------------------------------------------------
    def visit_Name(self, node: ast.Name) -> None:
        if node.id in BLOCKED_NAMES:
            raise SafetyViolation(f"'{node.id}' isn't available in this lesson yet.", node.lineno)
        self._check_identifier(node.id, node)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if _is_dunder(node.attr) or node.attr in BLOCKED_ATTRIBUTES:
            raise SafetyViolation(INTERNAL_NAME_MESSAGE, node.lineno)
        if node.attr.startswith("_") and node.attr not in ALLOWED_PRIVATE_ATTRIBUTES:
            raise SafetyViolation(PRIVATE_NAME_MESSAGE, node.lineno)
        self.generic_visit(node)

    # -- every other place an identifier can be bound -------------------------
    def visit_arg(self, node: ast.arg) -> None:
        self._check_identifier(node.arg, node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._check_identifier(node.name, node)
        for statement in node.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._class_body_methods.add(id(statement))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if id(node) not in self._class_body_methods:
            self._check_identifier(node.name, node)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_Global(self, node: ast.Global) -> None:
        for name in node.names:
            self._check_identifier(name, node)

    visit_Nonlocal = visit_Global  # type: ignore[assignment]

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self._check_identifier(node.name, node)
        self.generic_visit(node)

    def visit_MatchAs(self, node: ast.MatchAs) -> None:
        self._check_identifier(node.name, node)
        self.generic_visit(node)

    def visit_MatchStar(self, node: ast.MatchStar) -> None:
        self._check_identifier(node.name, node)
        self.generic_visit(node)

    # -- loops -------------------------------------------------------------------
    def visit_While(self, node: ast.While) -> None:
        if self.disallow_while:
            raise SafetyViolation(
                "A while loop here could run forever and freeze the game window — "
                "try game.after(...) to repeat something over time instead.",
                node.lineno,
            )
        self.generic_visit(node)


def check_code_safety(source: str, *, disallow_while: bool = False) -> None:
    """Raises SafetyViolation if the code uses something the sandbox blocks.

    Syntax errors are intentionally let through here — the real interpreter
    produces a much better, line-accurate syntax error for the child to see.

    disallow_while is used for graphical lessons: their top-level code must
    return control to the UI loop immediately (animation is done through
    game.after(...) callbacks), so a blocking loop is never what's wanted
    there regardless of which engine runs it.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return
    _SafetyVisitor(disallow_while=disallow_while).visit(tree)
