"""The restricted builtin set shared by the subprocess worker and the in-process
graphical runner. Kept in one place so the two execution paths can't drift apart."""
from __future__ import annotations

ALLOWED_BUILTIN_NAMES = [
    "print", "len", "range", "int", "float", "str", "bool", "list", "dict",
    "tuple", "set", "frozenset", "min", "max", "sum", "sorted", "abs", "round",
    "enumerate", "zip", "map", "filter", "True", "False", "None", "type",
    "isinstance", "issubclass", "reversed", "any", "all", "pow", "divmod",
    "chr", "ord", "repr", "format", "input", "Exception", "ValueError", "TypeError",
    "IndexError", "KeyError", "ZeroDivisionError", "StopIteration",
]
