"""Shared stubs and lookups for the Flet view tests.

FakePage stands in for ft.Page with just enough surface for the view
builders: update(), go() and run_task() (recorded, never executed --
there's no live event loop in tests). NoTaskPage is the same without
run_task, which exercises every motion helper's "can't animate, apply the
final state now" fallback (see app/ui/components/motion_flet.py).

Views tag their key controls with data={"kind": ...}; one()/all_of() find
them by role so tests don't depend on positional control-tree indexes.
"""
from __future__ import annotations

import flet as ft

from app.ui.components.adventure_kit_flet import find_by_kind, iter_controls


class FakePage:
    def __init__(self) -> None:
        self.update_count = 0
        self.routes_visited: list[str] = []
        self.run_task_calls: list = []

    def update(self) -> None:
        self.update_count += 1

    def go(self, route: str) -> None:
        self.routes_visited.append(route)

    def run_task(self, handler, *args, **kwargs) -> None:
        self.run_task_calls.append((handler, args, kwargs))

    def scheduled(self, handler) -> list[tuple]:
        """(args, kwargs) of every recorded run_task call for `handler`."""
        return [(args, kwargs) for h, args, kwargs in self.run_task_calls if h is handler]


class NoTaskPage(FakePage):
    """A page that can't schedule tasks -- motion helpers must degrade."""

    run_task = None  # type: ignore[assignment]


def all_of(root, kind: str) -> list:
    return find_by_kind(root, kind)


def one(root, kind: str):
    found = find_by_kind(root, kind)
    assert len(found) == 1, f"expected exactly one {kind!r}, found {len(found)}"
    return found[0]


def texts(root) -> list[str]:
    """Every non-empty ft.Text value under root, in tree order."""
    return [c.value for c in iter_controls(root) if isinstance(c, ft.Text) and c.value]
