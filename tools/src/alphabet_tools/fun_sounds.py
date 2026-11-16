"""Synthesizes the language-neutral fun sounds (our own work, so no license questions)."""

from collections.abc import Callable
from pathlib import Path

import numpy as np

from alphabet_tools.audio_processing import FloatAudio, encode_mp3

SAMPLE_RATE = 44100
PEAK = 0.8
NOISE_SEED = 7


def time_axis(seconds: float) -> FloatAudio:
    return np.linspace(0.0, seconds, int(SAMPLE_RATE * seconds), endpoint=False, dtype=np.float32)


def normalize(audio: FloatAudio) -> FloatAudio:
    return (audio / float(np.max(np.abs(audio))) * PEAK).astype(np.float32)


def boing() -> FloatAudio:
    t = time_axis(0.7)
    frequency = 180 + 260 * np.exp(-6 * t) * (1 + 0.25 * np.sin(2 * np.pi * 9 * t))
    phase = 2 * np.pi * np.cumsum(frequency) / SAMPLE_RATE
    return normalize(np.sin(phase) * np.exp(-4 * t))


def pop() -> FloatAudio:
    t = time_axis(0.18)
    frequency = 900 * np.exp(-18 * t) + 300
    phase = 2 * np.pi * np.cumsum(frequency) / SAMPLE_RATE
    return normalize(np.sin(phase) * np.exp(-30 * t))


def fart() -> FloatAudio:
    t = time_axis(0.9)
    rng = np.random.default_rng(NOISE_SEED)
    wobble = 1 + 0.35 * np.sin(2 * np.pi * 7 * t) + 0.1 * rng.standard_normal(t.size)
    frequency = (95 - 30 * t) * wobble
    phase = 2 * np.pi * np.cumsum(frequency) / SAMPLE_RATE
    buzz = np.sign(np.sin(phase)) * 0.6 + np.sin(phase) * 0.4
    envelope = np.minimum(t / 0.05, 1) * np.exp(-1.8 * t)
    return normalize(buzz * envelope)


def slide_whistle() -> FloatAudio:
    t = time_axis(0.6)
    frequency = 500 + 900 * t / t[-1]
    phase = 2 * np.pi * np.cumsum(frequency) / SAMPLE_RATE
    envelope = np.minimum(t / 0.03, 1) * np.minimum((t[-1] - t) / 0.08, 1)
    return normalize(np.sin(phase) * envelope)


FUN_SOUNDS: dict[str, Callable[[], FloatAudio]] = {
    "fun_boing": boing,
    "fun_pop": pop,
    "fun_fart": fart,
    "fun_whistle": slide_whistle,
}


def generate_fun_sounds(target_dir: Path) -> list[Path]:
    target_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, make in FUN_SOUNDS.items():
        path = target_dir / f"{name}.mp3"
        path.write_bytes(encode_mp3(make(), SAMPLE_RATE))
        written.append(path)
    return written
