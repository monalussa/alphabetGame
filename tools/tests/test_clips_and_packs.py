import json
from pathlib import Path

from alphabet_tools.checks import check_content
from alphabet_tools.clips import ManifestEntry, check_audio, list_clips, write_manifest
from alphabet_tools.loader import load_content
from alphabet_tools.pack_builder import build_packs
from alphabet_tools.paths import ContentPaths


def test_clips_cover_letter_names_characters_and_words(
    content_paths: ContentPaths, french: Path
) -> None:
    content, _ = load_content(content_paths)

    clip_ids = [clip.clip_id for clip in list_clips(content.languages["fr"])]

    assert clip_ids[:3] == ["letter_a", "word_ananas", "word_abeille"]
    assert "letter_w" in clip_ids


def test_missing_audio_is_warning_normally_and_error_when_strict(
    content_paths: ContentPaths, french: Path
) -> None:
    content, _ = load_content(content_paths)
    language = content.languages["fr"]

    relaxed = check_audio(language, content_paths, is_strict=False)
    strict = check_audio(language, content_paths, is_strict=True)

    assert [issue.severity for issue in relaxed] == ["warning"]
    assert [issue.severity for issue in strict] == ["error"]


def test_audio_with_changed_text_counts_as_outdated(
    content_paths: ContentPaths, french: Path
) -> None:
    content, _ = load_content(content_paths)
    language = content.languages["fr"]
    audio_dir = content_paths.audio_dir("fr")
    audio_dir.mkdir(parents=True)
    entries = {}
    for clip in list_clips(language):
        (audio_dir / f"{clip.clip_id}.mp3").write_bytes(b"mp3")
        entries[clip.clip_id] = ManifestEntry(clip.text, "recording", "0" * 64)
    entries["word_ananas"] = ManifestEntry("old text", "recording", "0" * 64)
    write_manifest(content_paths.audio_manifest_file("fr"), entries)

    issues = check_audio(language, content_paths, is_strict=True)

    assert len(issues) == 1
    assert "word_ananas" in issues[0].message


def test_build_writes_index_and_pack_with_emoji_fallback(
    content_paths: ContentPaths, french: Path
) -> None:
    content, _ = load_content(content_paths)
    assert check_content(content, content_paths) is not None

    build_packs(content, content_paths)

    index = json.loads((content_paths.output_dir / "packs" / "index.json").read_text())
    pack = json.loads((content_paths.output_dir / "packs" / "fr.json").read_text())
    first_entry = pack["letters"][0]["entries"][0]
    assert index["languages"] == [{"code": "fr", "name": "FR"}]
    assert first_entry == {
        "kind": "word",
        "id": "ananas",
        "text": "ananas",
        "caption": None,
        "image": None,
        "emoji": "🍎",
        "audio": None,
    }


def test_skipped_letter_is_not_playable(content_paths: ContentPaths, french: Path) -> None:
    content, _ = load_content(content_paths)

    build_packs(content, content_paths)

    pack = json.loads((content_paths.output_dir / "packs" / "fr.json").read_text())
    skipped = next(item for item in pack["letters"] if item["id"] == "w")
    assert skipped["isPlayable"] is False
    assert skipped["entries"] == []


def test_build_removes_stale_generated_files(content_paths: ContentPaths, french: Path) -> None:
    stale = content_paths.output_dir / "packs" / "old.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}")
    content, _ = load_content(content_paths)

    build_packs(content, content_paths)

    assert not stale.exists()
