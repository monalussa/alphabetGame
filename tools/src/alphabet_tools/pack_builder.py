"""Builds the runtime language packs the browser loads (public/packs, images, sounds)."""

import json
import shutil
from pathlib import Path
from typing import Any

from alphabet_tools.clips import (
    AUDIO_EXTENSION,
    clip_file,
    expected_source,
    is_clip_current,
    list_clips,
    read_manifest,
)
from alphabet_tools.model import Content, Language, Letter
from alphabet_tools.paths import ContentPaths

RUNTIME_SCHEMA_VERSION = 1
GENERATED_DIRS = ("packs", "images", "sounds")
CHARACTER_EXTENSION = ".svg"


def build_packs(content: Content, paths: ContentPaths) -> list[Path]:
    clean_output(paths.output_dir)
    written = [write_json(paths.output_dir / "packs" / "index.json", build_index(content))]
    fun_sounds = copy_fun_sounds(paths)
    for language in published_languages(content):
        pack = build_language_pack(language, content, paths, fun_sounds)
        written.append(write_json(paths.output_dir / "packs" / f"{language.code}.json", pack))
    copy_reviewed_images(content, paths)
    return written


def clean_output(output_dir: Path) -> None:
    for name in GENERATED_DIRS:
        target = output_dir / name
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)


def build_index(content: Content) -> dict[str, Any]:
    return {
        "schemaVersion": RUNTIME_SCHEMA_VERSION,
        "languages": [
            {"code": language.code, "name": language.name}
            for language in published_languages(content)
        ],
    }


def published_languages(content: Content) -> list[Language]:
    return [language for language in content.languages.values() if language.is_published]


def build_language_pack(
    language: Language, content: Content, paths: ContentPaths, fun_sounds: list[str]
) -> dict[str, Any]:
    available_audio = copy_current_audio(language, paths)
    available_characters = copy_characters(language, paths)
    return {
        "schemaVersion": RUNTIME_SCHEMA_VERSION,
        "code": language.code,
        "name": language.name,
        "locale": language.locale,
        "ui": language.ui_strings,
        "funSounds": fun_sounds,
        "letters": [
            build_letter(letter, content, available_audio, available_characters)
            for letter in language.letters
        ],
    }


def build_letter(
    letter: Letter, content: Content, audio: set[str], characters: set[str]
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    if letter.character is not None:
        character_id = f"char_{letter.id}"
        entries.append(
            {
                "kind": "character",
                "id": character_id,
                "text": letter.character.name,
                "caption": letter.character.line,
                "image": character_id if character_id in characters else None,
                "emoji": None,
                "audio": character_id if character_id in audio else None,
            }
        )
    for word in letter.words:
        concept = content.concepts[word.concept]
        record = content.images.get(concept.image_id) if concept.image_id else None
        has_image = record is not None and record.is_reviewed
        clip_id = f"word_{word.id}"
        entries.append(
            {
                "kind": "word",
                "id": word.id,
                "text": word.text,
                "caption": None,
                "image": concept.image_id if has_image else None,
                "emoji": None if has_image else concept.emoji,
                "audio": clip_id if clip_id in audio else None,
            }
        )
    letter_clip = f"letter_{letter.id}"
    return {
        "id": letter.id,
        "letter": letter.letter,
        "display": letter.display,
        "keys": list(letter.keys),
        "isPlayable": not letter.is_skipped and bool(entries),
        "audio": letter_clip if letter_clip in audio else None,
        "entries": entries,
    }


def copy_current_audio(language: Language, paths: ContentPaths) -> set[str]:
    manifest = read_manifest(paths.audio_manifest_file(language.code))
    source = expected_source(language)
    target_dir = paths.output_dir / "packs" / language.code / "audio"
    copied: set[str] = set()
    for clip in list_clips(language):
        file = clip_file(paths, language.code, clip.clip_id)
        if is_clip_current(clip, manifest.get(clip.clip_id), source, file):
            copy_regular_file(file, target_dir / f"{clip.clip_id}{AUDIO_EXTENSION}")
            copied.add(clip.clip_id)
    return copied


def copy_characters(language: Language, paths: ContentPaths) -> set[str]:
    source_dir = paths.characters_dir(language.code)
    target_dir = paths.output_dir / "packs" / language.code / "characters"
    copied: set[str] = set()
    for letter in language.letters:
        character_id = f"char_{letter.id}"
        file = source_dir / f"{character_id}{CHARACTER_EXTENSION}"
        if letter.character is not None and file.is_file():
            copy_regular_file(file, target_dir / file.name)
            copied.add(character_id)
    return copied


def copy_fun_sounds(paths: ContentPaths) -> list[str]:
    if not paths.fun_sounds_dir.is_dir():
        return []
    sounds = sorted(paths.fun_sounds_dir.glob(f"fun_*{AUDIO_EXTENSION}"))
    for file in sounds:
        copy_regular_file(file, paths.output_dir / "sounds" / file.name)
    return [file.stem for file in sounds]


def copy_reviewed_images(content: Content, paths: ContentPaths) -> None:
    for record in content.images.values():
        if record.is_reviewed:
            copy_regular_file(
                paths.images_dir / record.file, paths.output_dir / "images" / record.file
            )


def copy_regular_file(source: Path, target: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"refusing to copy non-regular file {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def write_json(path: Path, document: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    return path
