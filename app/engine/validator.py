"""Exercise validation: checks behavior/output, not exact code formatting."""
from __future__ import annotations

import ast
import re
from typing import Optional

INPUT_PLACEHOLDER = "{input}"

# Statement-level constructs a pattern can name that aren't expressible as a
# plain identifier in the AST (they're keywords, not Name nodes).
_KEYWORD_NODE_TYPES: dict[str, type[ast.AST]] = {
    "if": ast.If,
    "for": ast.For,
    "while": ast.While,
    "def": ast.FunctionDef,
    "return": ast.Return,
    "class": ast.ClassDef,
    "try": ast.Try,
    "with": ast.With,
    "global": ast.Global,
    "f-string": ast.JoinedStr,
}


def _dotted_attribute_name(node: ast.Attribute) -> str:
    """Reconstructs "inventory.append" from an Attribute node, or "" if the
    base isn't a plain name (e.g. a chained attribute/call result)."""
    if isinstance(node.value, ast.Name):
        return f"{node.value.id}.{node.attr}"
    return ""


class _ContainsVisitor(ast.NodeVisitor):
    def __init__(self, patterns: set[str]):
        self.remaining = set(patterns)

    def visit(self, node: ast.AST) -> None:
        if not self.remaining:
            return

        for keyword, node_type in _KEYWORD_NODE_TYPES.items():
            if keyword in self.remaining and isinstance(node, node_type):
                self.remaining.discard(keyword)

        if isinstance(node, ast.Name):
            self.remaining.discard(node.id)

        if isinstance(node, ast.Attribute):
            # Both "append" and "inventory.append" can name the same thing
            # -- the spec content itself uses both a bare method name
            # (canvas.forward -> "forward") and a full dotted path
            # (inventory.append -> "inventory.append") across examples.
            self.remaining.discard(node.attr)
            dotted = _dotted_attribute_name(node)
            if dotted:
                self.remaining.discard(dotted)

        if self.remaining:
            self.generic_visit(node)


def validate_ast_contains(code: str, patterns: list[str]) -> bool:
    """True if `code` contains every required construct in `patterns`.

    Each pattern is one of:
    - a statement keyword ("if", "for", "while", "def", "return", "class",
      "try", "with", "global") or "f-string" (an f"..." literal --
      ast.JoinedStr -- also not expressible as a plain identifier)
    - a dotted attribute path ("inventory.append", "ball.speed_x") --
      matches an attribute access on a plain name, whether it's a call
      (inventory.append(x)) or a plain read/assignment (ball.speed_x = 2)
    - a bare identifier ("print", "forward") -- matches that name used
      anywhere, including as the trailing part of a dotted access
      (canvas.forward(...) satisfies pattern "forward")

    A structural/pedagogical check (did the child use the construct the
    exercise asks for), not a precise static analyzer -- intentionally
    lenient about call-vs-reference so a correct-but-differently-shaped
    solution still passes. Code that fails to parse returns False rather
    than raising -- the sandbox's own syntax error handling already covers
    that case with a far better message for the child.
    """
    if not patterns:
        return True
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    visitor = _ContainsVisitor(set(patterns))
    visitor.visit(tree)
    return not visitor.remaining


def validate_output(
    actual_stdout: str,
    expected_output: str = "",
    input_value: Optional[str] = None,
    expected_output_pattern: Optional[str] = None,
) -> bool:
    """Compares output, optionally substituting what the child typed into a template.

    - expected_output_pattern (a regex) takes priority when set -- used for
      lessons involving randomness (games), where any of several outcomes is
      a valid, correctly-working program.
    - Otherwise expected_output can contain "{input}" as a placeholder for
      whatever the child entered, so any name/answer they try is accepted as
      long as their program echoes it back correctly.
    """
    actual = actual_stdout.strip()

    if expected_output_pattern:
        return re.fullmatch(expected_output_pattern, actual) is not None

    expected = expected_output
    if input_value is not None and INPUT_PLACEHOLDER in expected:
        expected = expected.replace(INPUT_PLACEHOLDER, input_value)
    return actual == expected.strip()
