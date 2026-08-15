"""One-off generator for this app's chime sounds -- run manually to
(re)produce the .wav files. No external audio-generation tool or asset is
used: each file is a short sequence of synthesized sine-wave notes with a
linear fade in/out (avoids clicks at note boundaries), written as plain
16-bit PCM mono WAV using only the stdlib (wave/struct/math). Not meant to
run as part of the app or the test suite.

Written to two places, mirroring how main-icon.png is already duplicated
in this repo: content/sounds/ is the canonical copy CTk reads via a plain
filesystem path (winsound.PlaySound), and assets/sounds/ is a copy of the
same files for Flet's asset pipeline (flet_audio.Audio's `src` is resolved
against ft.run()'s assets_dir, "assets" by default -- an arbitrary
filesystem path outside that dir isn't servable to the Flet client).
"""
from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 22050
FADE_SECONDS = 0.01

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIRS = [REPO_ROOT / "content" / "sounds", REPO_ROOT / "assets" / "sounds"]

# Each sound is a list of (frequency_hz, duration_seconds) notes played back to back.
SOUNDS: dict[str, list[tuple[float, float]]] = {
    "success_chime": [(523.25, 0.12), (659.25, 0.18)],  # C5 -> E5
    "badge_unlock": [(523.25, 0.10), (659.25, 0.10), (783.99, 0.20)],  # C5 -> E5 -> G5
    "level_up": [(523.25, 0.08), (659.25, 0.08), (783.99, 0.08), (1046.50, 0.22)],  # C5 -> E5 -> G5 -> C6
}


def _note_samples(frequency: float, duration: float) -> list[float]:
    n_samples = int(duration * SAMPLE_RATE)
    fade_samples = max(1, int(FADE_SECONDS * SAMPLE_RATE))
    samples = []
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        value = 0.5 * math.sin(2 * math.pi * frequency * t)
        if i < fade_samples:
            value *= i / fade_samples
        elif i > n_samples - fade_samples:
            value *= (n_samples - i) / fade_samples
        samples.append(value)
    return samples


def write_wav(path: Path, notes: list[tuple[float, float]]) -> None:
    samples: list[float] = []
    for frequency, duration in notes:
        samples.extend(_note_samples(frequency, duration))

    frames = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples)
    with wave.open(str(path), "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(frames)


def main() -> None:
    for out_dir in OUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, notes in SOUNDS.items():
            path = out_dir / f"{name}.wav"
            write_wav(path, notes)
            print(f"wrote {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
