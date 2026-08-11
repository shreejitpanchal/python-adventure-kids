"""Static (AST-based) safety check, run before any child code is executed.

This is the first of two layers — the worker process also runs with a
restricted builtins set as defense in depth.
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
# standard library. Everything else stays blocked.
ALLOWED_MODULES = {"random"}


class SafetyViolation(Exception):
    def __init__(self, message: str, line: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.line = line


class _SafetyVisitor(ast.NodeVisitor):
    def __init__(self, disallow_while: bool = False):
        self.disallow_while = disallow_while

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root_module = alias.name.split(".")[0]
            if root_module not in ALLOWED_MODULES:
                raise SafetyViolation(
                    f"Importing '{alias.name}' isn't allowed in lessons yet.", node.lineno
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        root_module = (node.module or "").split(".")[0]
        if root_module not in ALLOWED_MODULES:
            raise SafetyViolation(
                f"Importing from '{node.module}' isn't allowed in lessons yet.", node.lineno
            )
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in BLOCKED_NAMES:
            raise SafetyViolation(f"'{node.id}' isn't available in this lesson yet.", node.lineno)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("__") and node.attr.endswith("__"):
            raise SafetyViolation("Using names like this isn't allowed.", node.lineno)
        self.generic_visit(node)

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

    disallow_while is used for graphical lessons, which run in-process (no OS
    timeout can save us from a runaway loop there) rather than in the
    subprocess sandbox.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return
    _SafetyVisitor(disallow_while=disallow_while).visit(tree)
