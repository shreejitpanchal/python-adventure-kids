"""Plays this app's chime sounds (see app/audio/player.py for which sound
means what) on Flet, via the flet_audio package.

flet_audio.Audio is a non-visual "service" control -- Flet's own examples
add one instance per sound to page.overlay once, then call its play()
method from event handlers. play() is declared `async def` in the
installed flet_audio==0.86.5, so it can't just be called bare from a sync
handler (that would leave the coroutine unawaited and silently do
nothing) -- page.run_task() is Flet's own documented way to fire an async
control method from sync code, scheduling it onto the page's real event
loop (the same shape as app/games/game_canvas_flet.py's after(), which
schedules via that loop directly).

One instance is built per app session (in app_window_flet.main(), stored
on AppState.sound_player) rather than per screen, since each Audio control
registers itself in page.overlay on construction -- building a fresh one
every time a lesson screen is opened would leak an Audio control into
page.overlay on every single lesson visit.

Sound files must live under this app's Flet assets_dir ("assets/",
ft.run()'s default -- see main_flet.py) to be servable to the client at
all; content/sounds/ (what CTk's winsound-based player reads directly)
isn't reachable from here. scripts/generate_sounds.py writes the same
files to both assets/sounds/ and content/sounds/ for exactly this reason.
"""
from __future__ import annotations

import flet as ft
import flet_audio as fa

from app.audio.player import SOUND_NAMES
from app.config.settings import Settings


class SoundPlayerFlet:
    def __init__(self, page: ft.Page) -> None:
        self._page = page
        self._audio_controls: dict[str, fa.Audio] = {
            name: fa.Audio(src=f"sounds/{name}.wav") for name in SOUND_NAMES
        }
        page.overlay.extend(self._audio_controls.values())

    def play(self, name: str, settings: Settings) -> None:
        """Fire-and-forget. No-ops quietly if sound is disabled or `name`
        isn't a known sound -- a missing/disabled sound should never be a
        reason a lesson can't be completed."""
        if not settings.sound_enabled:
            return
        audio = self._audio_controls.get(name)
        if audio is None:
            return
        self._page.run_task(audio.play)
