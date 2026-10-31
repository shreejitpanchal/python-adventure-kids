"""Haptic feedback for the Flet game-world UI: a tick on taps, a thump on
a passed lesson, a buzz on a reward. Flet only -- there is no CTk
equivalent (desktop Windows has no vibration motor), and on a desktop
Flet client every call is a silent no-op, so screens can fire these
without caring where they run.

ft.HapticFeedback is one of Flet's core (non-visual) Service controls:
like ft.FilePicker/ft.Share in settings_screen_flet.py it registers
itself with the current page session the moment it is constructed, so
the service is built lazily on first use -- never up front in
app_window_flet.main(), and never via page.overlay (the path that broke
ft.FilePicker on Android, see app_window_flet.py). Its impact methods are
`async def`, so they are fired through page.run_task() the same way
sound_player_flet.py fires Audio.play().

Every call is guarded twice: by the child's Settings toggle
(Settings.haptics_enabled, "📳 Vibration" in Settings) and by a broad
except -- a client without the service, or one that rejects the call, must
never be a reason a tap doesn't navigate or a lesson can't be completed.
"""
from __future__ import annotations

from typing import Optional

import flet as ft

from app.config.settings import Settings


class HapticsFlet:
    def __init__(self, page: ft.Page) -> None:
        self._page = page
        self._service: Optional[object] = None
        self._unavailable = False

    def _ensure_service(self):
        if self._service is None and not self._unavailable:
            factory = getattr(ft, "HapticFeedback", None)
            if factory is None:
                self._unavailable = True
                return None
            try:
                self._service = factory()
            except Exception:  # noqa: BLE001 -- see module docstring
                self._unavailable = True
                return None
        return self._service

    def _fire(self, method_name: str, settings: Settings) -> bool:
        """Schedules one impact; False when haptics are off, unavailable, or
        the page can't run tasks (tests' NoTaskPage)."""
        if not getattr(settings, "haptics_enabled", True):
            return False
        run_task = getattr(self._page, "run_task", None)
        if run_task is None:
            return False
        service = self._ensure_service()
        if service is None:
            return False
        method = getattr(service, method_name, None)
        if method is None:
            return False
        try:
            run_task(method)
        except Exception:  # noqa: BLE001
            return False
        return True

    def tap(self, settings: Settings) -> bool:
        """A light tick -- pressing a card, node or chunky button."""
        return self._fire("light_impact", settings)

    def error(self, settings: Settings) -> bool:
        """A firmer bump -- a run that errored or printed the wrong thing."""
        return self._fire("medium_impact", settings)

    def success(self, settings: Settings) -> bool:
        """A solid thump -- a lesson passed."""
        return self._fire("heavy_impact", settings)

    def reward(self, settings: Settings) -> bool:
        """The long buzz -- chest opened, quest bonus claimed, level up."""
        return self._fire("vibrate", settings)
