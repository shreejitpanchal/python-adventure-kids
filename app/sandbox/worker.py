"""Runs in its own subprocess with a restricted builtin set. Never imported by the app directly.

Invoked as: python -I worker.py <path-to-child-code.py>
Second layer of defense — app/sandbox/safety.py already statically rejected
anything obviously dangerous before this process was even spawned.
"""
from __future__ import annotations

import builtins
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.sandbox.allowed_builtins import ALLOWED_BUILTIN_NAMES

# Kept in sync with app/sandbox/safety.py's ALLOWED_MODULES -- that AST check
# already rejects anything else before this process is even spawned; this is
# the second, defense-in-depth layer.
ALLOWED_MODULES = {"random"}


def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    root_module = name.split(".")[0]
    if root_module not in ALLOWED_MODULES:
        raise ImportError(f"Importing '{name}' is not allowed here yet.")
    return builtins.__import__(name, globals, locals, fromlist, level)


def build_safe_globals() -> dict:
    safe_builtins = {
        name: getattr(builtins, name) for name in ALLOWED_BUILTIN_NAMES if hasattr(builtins, name)
    }
    safe_builtins["__import__"] = _restricted_import
    return {"__builtins__": safe_builtins}


def main() -> None:
    if len(sys.argv) != 2:
        print("worker: missing code file argument", file=sys.stderr)
        sys.exit(2)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        source = f.read()

    compiled = compile(source, "<your code>", "exec")
    exec(compiled, build_safe_globals())


if __name__ == "__main__":
    main()
