"""The restricted runtime environment every execution engine hands child
code: the allowed builtins, plus the restricted `__import__` that serves
only the allowlisted stdlib modules -- and only a *view* of each.

Kept in one place so the subprocess worker (app/sandbox/worker.py) and the
in-process runner (app/sandbox/inprocess_runner.py) can't drift apart.
Before this was shared, each engine hand-copied the module allowlist and
its own `_restricted_import`, and neither hid a module's private or
submodule attributes: `random._os` *is* the os module, `collections._sys`
is sys, and `json.decoder.re.enum.sys` walks to sys through nothing but
public names. app/sandbox/safety.py's AST rules reject the private-name
spellings; the module views built here make sure the objects aren't there
at runtime either, so a spelling the AST check didn't anticipate has
nothing to find.
"""
from __future__ import annotations

import builtins
import types
from typing import Callable, Mapping, Optional

from app.sandbox.safety import ALLOWED_MODULES

ALLOWED_BUILTIN_NAMES = [
    "print", "len", "range", "int", "float", "str", "bool", "list", "dict",
    "tuple", "set", "frozenset", "min", "max", "sum", "sorted", "abs", "round",
    "enumerate", "zip", "map", "filter", "True", "False", "None", "type",
    "isinstance", "issubclass", "reversed", "any", "all", "pow", "divmod",
    "chr", "ord", "repr", "format", "input", "Exception", "ValueError", "TypeError",
    "IndexError", "KeyError", "ZeroDivisionError", "StopIteration",
]

ModuleOverrides = Mapping[str, Mapping[str, object]]
"""module name -> {attribute name -> replacement}. Lets an engine swap one
attribute of an allowlisted module for a sandbox-aware version -- the
in-process runner replaces time.sleep with one its watchdog can interrupt."""


def make_module_view(
    module: types.ModuleType, overrides: Optional[Mapping[str, object]] = None
) -> types.SimpleNamespace:
    """A plain namespace holding only `module`'s public, non-module
    attributes. Public functions and classes come through untouched
    (random.randint, collections.Counter, json.dumps); leading-underscore
    names and anything that is itself a module are left out, which is what
    closes the random._os / json.decoder escape routes."""
    public = {
        name: value
        for name, value in vars(module).items()
        if not name.startswith("_") and not isinstance(value, types.ModuleType)
    }
    if overrides:
        public.update(overrides)
    return types.SimpleNamespace(**public)


def make_restricted_import(
    module_overrides: Optional[ModuleOverrides] = None,
) -> Callable[..., types.SimpleNamespace]:
    """The `__import__` replacement installed in child code's builtins.

    Only a bare allowlisted top-level name is accepted -- no dotted
    submodule imports (`import json.decoder`), no relative imports. Views
    are built lazily and cached on the returned function, i.e. per run, so
    child code that mutates a view (`random.randint = None`) affects only
    its own run, never the next one.
    """
    views: dict[str, types.SimpleNamespace] = {}

    def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level != 0 or name not in ALLOWED_MODULES:
            raise ImportError(f"Importing '{name}' is not allowed here yet.")
        if name not in views:
            overrides = (module_overrides or {}).get(name)
            views[name] = make_module_view(builtins.__import__(name), overrides)
        return views[name]

    return restricted_import


def build_safe_builtins(module_overrides: Optional[ModuleOverrides] = None) -> dict:
    """The `__builtins__` mapping for one sandboxed run: exactly
    ALLOWED_BUILTIN_NAMES plus the restricted `__import__`. Engines may add
    their own `input` replacement on top (the in-process runner feeds it
    from the lesson's answer box)."""
    safe_builtins = {
        name: getattr(builtins, name) for name in ALLOWED_BUILTIN_NAMES if hasattr(builtins, name)
    }
    safe_builtins["__import__"] = make_restricted_import(module_overrides)
    return safe_builtins
