"""Inventory of audio clips each language needs, and the manifest of generated clips."""

import json
from dataclasses import dataclass
from pathlib import Path

from alphabet_tools.issues import Issue, error, warning
from alphabet_tools.model import Language
from alphabet_tools.paths import ContentPaths

AUDIO_EXTENSION = ".mp3"
MANIFEST_SCHEMA_REF = "../../schemas/audio-manifest.schema.json"


@dataclass(frozen=True)
class Clip:
    clip_id: str
    text: str


@dataclass(frozen=True)
class ManifestEntry:
    text: str
    source: str
    fingerprint: str


def list_clips(language: Language) -> list[Clip]:
    clips: list[Clip] = []
    for letter in language.letters:
        clips.append(Clip(f"letter_{letter.id}", letter.name))
        if letter.character is not None:
            clips.append(Clip(f"char_{letter.id}", letter.character.spoken_text))
        clips += [Clip(f"word_{word.id}", word.spoken_text) for word in letter.words]
    return clips


def expected_source(language: Language) -> str:
    if language.audio.source == "piper":
        return f"piper:{language.audio.voice}"
    return "recording"


def clip_file(paths: ContentPaths, code: str, clip_id: str) -> Path:
    return paths.audio_dir(code) / f"{clip_id}{AUDIO_EXTENSION}"


def read_manifest(path: Path) -> dict[str, ManifestEntry]:
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {clip_id: ManifestEntry(**entry) for clip_id, entry in raw["clips"].items()}


def write_manifest(path: Path, entries: dict[str, ManifestEntry]) -> None:
    document = {
        "$schema": MANIFEST_SCHEMA_REF,
        "clips": {
            clip_id: {"text": e.text, "source": e.source, "fingerprint": e.fingerprint}
            for clip_id, e in sorted(entries.items())
        },
    }
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def is_clip_current(clip: Clip, entry: ManifestEntry | None, source: str, file: Path) -> bool:
    return (
        entry is not None and entry.text == clip.text and entry.source == source and file.is_file()
    )


def check_audio(language: Language, paths: ContentPaths, is_strict: bool) -> list[Issue]:
    manifest = read_manifest(paths.audio_manifest_file(language.code))
    source = expected_source(language)
    report = error if is_strict else warning
    issues: list[Issue] = []
    missing = [
        clip.clip_id
        for clip in list_clips(language)
        if not is_clip_current(
            clip, manifest.get(clip.clip_id), source, clip_file(paths, language.code, clip.clip_id)
        )
    ]
    if missing:
        preview = ", ".join(missing[:5]) + (" …" if len(missing) > 5 else "")
        issues.append(
            report(f"{language.code}/audio", f"{len(missing)} clips missing or outdated: {preview}")
        )
    known = {clip.clip_id for clip in list_clips(language)}
    audio_dir = paths.audio_dir(language.code)
    if audio_dir.is_dir():
        issues += [
            warning(f"{language.code}/audio", f"unused file {file.name}")
            for file in sorted(audio_dir.glob(f"*{AUDIO_EXTENSION}"))
            if file.stem not in known
        ]
    return issues
