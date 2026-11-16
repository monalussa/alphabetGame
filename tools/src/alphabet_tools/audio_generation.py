"""Creates the MP3 clips of one language from Piper speech or from the owner's recordings."""

import hashlib
import logging
import wave
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path

import numpy as np

from alphabet_tools.audio_processing import (
    FloatAudio,
    encode_mp3,
    fingerprint,
    process_speech,
)
from alphabet_tools.clips import (
    Clip,
    ManifestEntry,
    clip_file,
    expected_source,
    list_clips,
    read_manifest,
    write_manifest,
)
from alphabet_tools.model import Language
from alphabet_tools.paths import ContentPaths

logger = logging.getLogger(__name__)

DEFAULT_LENGTH_SCALE = 1.15
PCM_16_BIT_WIDTH = 2
INT16_SCALE = 32768.0


@dataclass
class GenerationReport:
    generated: int = 0
    unchanged: int = 0
    missing_recordings: int = 0


class RecordingError(Exception):
    """A recording is not a mono or stereo 16-bit PCM WAV file."""


def generate_language_audio(
    language: Language, paths: ContentPaths, should_force: bool
) -> GenerationReport:
    manifest_path = paths.audio_manifest_file(language.code)
    manifest = read_manifest(manifest_path)
    paths.audio_dir(language.code).mkdir(parents=True, exist_ok=True)
    synthesizer = PiperSynthesizer(language) if language.audio.source == "piper" else None
    report = GenerationReport()
    try:
        for clip in list_clips(language):
            entry = produce_clip(
                clip, language, paths, manifest.get(clip.clip_id), synthesizer, should_force
            )
            if entry is None:
                report.missing_recordings += 1
            elif entry is manifest.get(clip.clip_id):
                report.unchanged += 1
            else:
                manifest[clip.clip_id] = entry
                report.generated += 1
    finally:
        write_manifest(manifest_path, manifest)
    return report


def produce_clip(
    clip: Clip,
    language: Language,
    paths: ContentPaths,
    current: ManifestEntry | None,
    synthesizer: "PiperSynthesizer | None",
    should_force: bool,
) -> ManifestEntry | None:
    target = clip_file(paths, language.code, clip.clip_id)
    source = expected_source(language)
    plan = plan_clip(clip, language, paths, source, synthesizer)
    if plan is None:
        return None
    new_fingerprint, load_audio = plan

    is_unchanged = (
        current is not None
        and current.fingerprint == new_fingerprint
        and current.text == clip.text
        and target.is_file()
    )
    if is_unchanged and not should_force:
        return current
    audio, sample_rate = load_audio()
    target.write_bytes(encode_mp3(process_speech(audio, sample_rate), sample_rate))
    logger.info("clip written", extra={"clip_id": clip.clip_id, "language": language.code})
    return ManifestEntry(text=clip.text, source=source, fingerprint=new_fingerprint)


AudioLoader = Callable[[], tuple[FloatAudio, int]]


def plan_clip(
    clip: Clip,
    language: Language,
    paths: ContentPaths,
    source: str,
    synthesizer: "PiperSynthesizer | None",
) -> tuple[str, AudioLoader] | None:
    """Fingerprint of the clip's input and how to load its audio; None if no recording yet."""
    if synthesizer is not None:
        piper_fingerprint = fingerprint(
            text=clip.text, source=source, scale=synthesizer.length_scale
        )
        return piper_fingerprint, partial(synthesizer.synthesize, clip.text)
    recording = paths.recordings_dir(language.code) / f"{clip.clip_id}.wav"
    if not recording.is_file():
        return None
    recording_digest = hashlib.sha256(recording.read_bytes()).hexdigest()
    return fingerprint(recording=recording_digest), partial(read_wav, recording)


class PiperSynthesizer:
    def __init__(self, language: Language) -> None:
        from piper import PiperVoice, SynthesisConfig

        from alphabet_tools.voices import ensure_voice

        if language.audio.voice is None:
            raise ValueError(f"{language.code}: piper audio needs a voice")
        self.length_scale = language.audio.length_scale or DEFAULT_LENGTH_SCALE
        self._voice = PiperVoice.load(ensure_voice(language.audio.voice))
        self._config = SynthesisConfig(length_scale=self.length_scale)

    def synthesize(self, text: str) -> tuple[FloatAudio, int]:
        chunks = list(self._voice.synthesize(text, syn_config=self._config))
        if not chunks:
            raise ValueError(f"piper produced no audio for {text!r}")
        audio = np.concatenate([chunk.audio_float_array for chunk in chunks]).astype(np.float32)
        return audio, chunks[0].sample_rate


def read_wav(path: Path) -> tuple[FloatAudio, int]:
    with wave.open(str(path), "rb") as wav:
        if wav.getsampwidth() != PCM_16_BIT_WIDTH or wav.getnchannels() not in (1, 2):
            raise RecordingError(f"{path.name}: expected 16-bit mono/stereo PCM WAV")
        frames = wav.readframes(wav.getnframes())
        channels = wav.getnchannels()
        sample_rate = wav.getframerate()
    samples = np.frombuffer(frames, dtype="<i2").astype(np.float32) / INT16_SCALE
    if channels == 2:
        samples = samples.reshape(-1, 2).mean(axis=1)
    return samples.astype(np.float32), sample_rate
