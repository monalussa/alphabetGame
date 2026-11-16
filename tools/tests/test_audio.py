import wave
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from alphabet_tools.audio_generation import generate_language_audio
from alphabet_tools.audio_processing import (
    PEAK_LIMIT,
    encode_mp3,
    fingerprint,
    level,
    trim_silence,
)
from alphabet_tools.clips import read_manifest
from alphabet_tools.loader import load_content
from alphabet_tools.paths import ContentPaths
from alphabet_tools.voices import VoiceError, ensure_file

SAMPLE_RATE = 16000


def tone(seconds: float, amplitude: float = 0.5) -> np.ndarray:
    t = np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE
    return (amplitude * np.sin(2 * np.pi * 440 * t)).astype(np.float32)


def silence(seconds: float) -> np.ndarray:
    return np.zeros(int(seconds * SAMPLE_RATE), dtype=np.float32)


def write_wav(path: Path, audio: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes((audio * 32767).astype("<i2").tobytes())


def test_trim_silence_removes_leading_and_trailing_silence() -> None:
    audio = np.concatenate([silence(1), tone(0.5), silence(1)])

    trimmed = trim_silence(audio, SAMPLE_RATE)

    assert 0.5 <= trimmed.size / SAMPLE_RATE < 0.6


def test_trim_silence_of_pure_silence_is_empty() -> None:
    assert trim_silence(silence(1), SAMPLE_RATE).size == 0


def test_level_never_exceeds_peak_limit() -> None:
    leveled = level(tone(0.5, amplitude=0.01))

    assert float(np.max(np.abs(leveled))) <= PEAK_LIMIT + 1e-6


def test_encode_mp3_produces_mp3_frames() -> None:
    encoded = encode_mp3(tone(0.3), SAMPLE_RATE)

    assert encoded[:3] == b"ID3" or (encoded[0] == 0xFF and encoded[1] & 0xE0 == 0xE0)


def test_fingerprint_changes_when_text_changes() -> None:
    assert fingerprint(text="ananas") != fingerprint(text="avion")


def test_recordings_become_clips_and_are_not_regenerated(
    content_paths: ContentPaths, french: Path
) -> None:
    write_wav(content_paths.recordings_dir("fr") / "word_ananas.wav", tone(0.4))
    language = load_content(content_paths)[0].languages["fr"]

    first = generate_language_audio(language, content_paths, should_force=False)
    second = generate_language_audio(language, content_paths, should_force=False)

    assert (first.generated, first.missing_recordings) == (1, 6)
    assert (second.generated, second.unchanged) == (0, 1)
    assert (content_paths.audio_dir("fr") / "word_ananas.mp3").is_file()
    assert read_manifest(content_paths.audio_manifest_file("fr"))["word_ananas"].text == "ananas"


def test_voice_download_from_unexpected_host_is_refused(tmp_path: Path) -> None:
    with pytest.raises(VoiceError, match="unexpected URL"):
        ensure_file("https://evil.example/voice.onnx", tmp_path / "voice.onnx", "0" * 64)


def test_voice_with_wrong_checksum_is_rejected_and_not_kept(tmp_path: Path) -> None:
    target = tmp_path / "voice.onnx"
    url = "https://huggingface.co/rhasspy/piper-voices/resolve/abc/voice.onnx"

    class FakeResponse:
        def __init__(self) -> None:
            self._chunks = [b"tampered", b""]

        def read(self, _size: int = -1) -> bytes:
            return self._chunks.pop(0)

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    with (
        patch("urllib.request.urlopen", return_value=FakeResponse()),
        pytest.raises(VoiceError, match="checksum mismatch"),
    ):
        ensure_file(url, target, "0" * 64)

    assert not target.exists()
    assert list(tmp_path.iterdir()) == []
