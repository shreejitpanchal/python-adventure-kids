"""app/audio/player.py: the shared sound-selection decision logic (pure,
platform-agnostic) and the CTk playback path. The actual OS-level call
(winsound.PlaySound) is monkeypatched so the test suite stays silent and
doesn't depend on a real audio device -- only that the right file path
and flags would have been passed, and that the settings/platform guards
correctly skip playback."""
from __future__ import annotations

import wave

import pytest

from app.audio.player import SOUND_NAMES, play_sound_ctk, sound_path, success_sound_for
from app.config.settings import Settings


# -- success_sound_for() ---------------------------------------------------
def test_plain_success_plays_only_the_chime():
    assert success_sound_for(leveled_up=False, badge_earned=False) == ["success_chime"]


def test_level_up_takes_priority_over_the_plain_chime():
    assert success_sound_for(leveled_up=True, badge_earned=False) == ["level_up"]


def test_badge_layers_on_top_of_a_plain_success():
    assert success_sound_for(leveled_up=False, badge_earned=True) == ["success_chime", "badge_unlock"]


def test_badge_layers_on_top_of_a_level_up():
    assert success_sound_for(leveled_up=True, badge_earned=True) == ["level_up", "badge_unlock"]


# -- sound_path() -------------------------------------------------------------
@pytest.mark.parametrize("name", SOUND_NAMES)
def test_sound_path_points_at_a_real_wav_file(name):
    path = sound_path(name)
    assert path.suffix == ".wav"
    assert path.is_file()


def test_sound_path_rejects_an_unknown_name():
    with pytest.raises(ValueError):
        sound_path("explosion")


@pytest.mark.parametrize("name", SOUND_NAMES)
def test_generated_wav_files_are_valid_and_short(name):
    path = sound_path(name)
    with wave.open(str(path), "rb") as f:
        assert f.getnchannels() == 1
        duration = f.getnframes() / f.getframerate()
        assert 0 < duration < 2.0


# -- play_sound_ctk() -----------------------------------------------------
def test_play_sound_ctk_calls_winsound_when_enabled(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    calls = []

    class FakeWinsound:
        SND_FILENAME = 1
        SND_ASYNC = 2

        @staticmethod
        def PlaySound(path, flags):
            calls.append((path, flags))

    monkeypatch.setitem(__import__("sys").modules, "winsound", FakeWinsound)

    play_sound_ctk("success_chime", Settings(sound_enabled=True))

    assert len(calls) == 1
    path, flags = calls[0]
    assert path.endswith("success_chime.wav")
    assert flags == FakeWinsound.SND_FILENAME | FakeWinsound.SND_ASYNC


def test_play_sound_ctk_no_ops_when_sound_disabled(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    calls = []

    class FakeWinsound:
        SND_FILENAME = 1
        SND_ASYNC = 2

        @staticmethod
        def PlaySound(path, flags):
            calls.append((path, flags))

    monkeypatch.setitem(__import__("sys").modules, "winsound", FakeWinsound)

    play_sound_ctk("success_chime", Settings(sound_enabled=False))

    assert calls == []


def test_play_sound_ctk_no_ops_on_non_windows(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    # No winsound patched in -- if the guard didn't skip, importing it
    # would raise ModuleNotFoundError on a non-Windows test machine, or
    # here just prove it's never reached.
    play_sound_ctk("success_chime", Settings(sound_enabled=True))
