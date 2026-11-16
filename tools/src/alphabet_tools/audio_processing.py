"""Turns raw speech into consistent, small MP3 clips: trim, level, fade, pad, encode."""

import hashlib
import json

import lameenc
import numpy as np
import numpy.typing as npt

FloatAudio = npt.NDArray[np.float32]

PROCESSING_VERSION = 1
SILENCE_THRESHOLD_RATIO = 0.03
TRIM_MARGIN_SECONDS = 0.04
LEAD_IN_SECONDS = 0.08
FADE_SECONDS = 0.01
TARGET_RMS = 0.1
PEAK_LIMIT = 0.89
MP3_BITRATE_KBPS = 48
MP3_QUALITY = 2
INT16_MAX = 32767


def trim_silence(audio: FloatAudio, sample_rate: int) -> FloatAudio:
    if audio.size == 0:
        return audio
    threshold = float(np.max(np.abs(audio))) * SILENCE_THRESHOLD_RATIO
    loud = np.flatnonzero(np.abs(audio) > threshold)
    if loud.size == 0:
        return audio[:0]
    margin = int(TRIM_MARGIN_SECONDS * sample_rate)
    start = max(int(loud[0]) - margin, 0)
    end = min(int(loud[-1]) + margin + 1, audio.size)
    return audio[start:end]


def level(audio: FloatAudio) -> FloatAudio:
    rms = float(np.sqrt(np.mean(np.square(audio)))) if audio.size else 0.0
    if rms == 0.0:
        return audio
    scaled = audio * (TARGET_RMS / rms)
    peak = float(np.max(np.abs(scaled)))
    if peak > PEAK_LIMIT:
        scaled = scaled * (PEAK_LIMIT / peak)
    return scaled.astype(np.float32)


def fade_and_pad(audio: FloatAudio, sample_rate: int) -> FloatAudio:
    fade_length = min(int(FADE_SECONDS * sample_rate), audio.size // 2)
    faded = audio.copy()
    if fade_length > 0:
        ramp = np.linspace(0.0, 1.0, fade_length, dtype=np.float32)
        faded[:fade_length] *= ramp
        faded[-fade_length:] *= ramp[::-1]
    lead_in = np.zeros(int(LEAD_IN_SECONDS * sample_rate), dtype=np.float32)
    return np.concatenate([lead_in, faded])


def process_speech(audio: FloatAudio, sample_rate: int) -> FloatAudio:
    return fade_and_pad(level(trim_silence(audio, sample_rate)), sample_rate)


def encode_mp3(audio: FloatAudio, sample_rate: int) -> bytes:
    pcm = (np.clip(audio, -1.0, 1.0) * INT16_MAX).astype("<i2").tobytes()
    encoder = lameenc.Encoder()
    encoder.set_bit_rate(MP3_BITRATE_KBPS)
    encoder.set_in_sample_rate(sample_rate)
    encoder.set_channels(1)
    encoder.set_quality(MP3_QUALITY)
    return bytes(encoder.encode(pcm) + encoder.flush())


def fingerprint(**parts: object) -> str:
    payload = json.dumps({**parts, "processing": PROCESSING_VERSION}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
