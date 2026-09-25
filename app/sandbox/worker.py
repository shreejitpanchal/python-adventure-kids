"""Runs in its own subprocess with a restricted builtin set. Never imported by the app directly.

Invoked as: python -I worker.py <path-to-child-code.py>
Second layer of defense — app/sandbox/safety.py already statically rejected
anything obviously dangerous before this process was even spawned. The
restricted environment itself (allowed builtins, allowlisted-module views)
comes from app/sandbox/allowed_builtins.py, shared with the in-process
engine so the two can't drift apart.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.sandbox.allowed_builtins import build_safe_builtins


def build_safe_globals() -> dict:
    return {"__builtins__": build_safe_builtins()}


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
