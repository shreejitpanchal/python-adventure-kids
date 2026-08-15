import builtins

from app.audio.player import SOUND_NAMES
from app.config.settings import Settings
from app.ui.components.sound_player_flet import SoundPlayerFlet


class FakePage:
    def __init__(self) -> None:
        self.overlay: list = []
        self.run_task_calls: list = []

    def run_task(self, handler, *args, **kwargs) -> None:
        self.run_task_calls.append((handler, args, kwargs))


def test_constructing_registers_one_audio_control_per_sound_in_overlay():
    page = FakePage()
    SoundPlayerFlet(page)
    assert len(page.overlay) == len(SOUND_NAMES)


def test_play_schedules_the_audio_controls_play_method_via_run_task():
    page = FakePage()
    player = SoundPlayerFlet(page)

    player.play("success_chime", Settings(sound_enabled=True))

    assert len(page.run_task_calls) == 1
    handler, _args, _kwargs = page.run_task_calls[0]
    assert handler == player._audio_controls["success_chime"].play


def test_play_no_ops_when_sound_disabled():
    page = FakePage()
    player = SoundPlayerFlet(page)

    player.play("success_chime", Settings(sound_enabled=False))

    assert page.run_task_calls == []


def test_play_no_ops_for_an_unknown_sound_name():
    page = FakePage()
    player = SoundPlayerFlet(page)

    player.play("explosion", Settings(sound_enabled=True))

    assert page.run_task_calls == []


def test_missing_flet_audio_package_degrades_gracefully_instead_of_crashing(monkeypatch):
    """A packaged build (Android/iOS, or any run mode that bundles its own
    requirements) can, in practice, be built from a snapshot that predates
    flet_audio being added as a dependency -- the whole app must still
    start, just with sound silently unavailable, not crash at import time."""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "flet_audio":
            raise ImportError("No module named 'flet_audio'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    page = FakePage()
    player = SoundPlayerFlet(page)  # must not raise

    assert page.overlay == []
    player.play("success_chime", Settings(sound_enabled=True))  # must not raise
    assert page.run_task_calls == []
