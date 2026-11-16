import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from alphabet_tools.paths import DEFAULT_PATHS, ContentPaths

UI_STRINGS = {"app.title": "Titre", "start.play": "Jouer"}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def word(word_id: str, text: str, concept: str = "apple") -> dict[str, str]:
    return {"id": word_id, "text": text, "concept": concept}


def letter(letter_id: str, words: list[dict[str, str]], **extra: Any) -> dict[str, Any]:
    value = extra.pop("letter", letter_id)
    return {
        "id": letter_id,
        "letter": value,
        "display": f"{value.upper()} {value}",
        "name": value,
        "keys": extra.pop("keys", [value]),
        **({"words": words} if words else {"skip": True}),
        **extra,
    }


@pytest.fixture
def content_paths(tmp_path: Path) -> ContentPaths:
    paths = ContentPaths(content_dir=tmp_path / "content", output_dir=tmp_path / "public")
    shutil.copytree(DEFAULT_PATHS.schemas_dir, paths.schemas_dir)
    write_json(
        paths.concepts_file, {"concepts": {"apple": {"emoji": "🍎"}, "ant": {"emoji": "🐜"}}}
    )
    write_json(paths.image_manifest_file, {"images": []})
    return paths


LanguageWriter = Callable[..., Path]


@pytest.fixture
def write_language(content_paths: ContentPaths) -> LanguageWriter:
    def write(
        code: str,
        letters: list[dict[str, Any]],
        *,
        match_accents: bool = False,
        audio: dict[str, str] | None = None,
        ui: dict[str, str] | None = None,
    ) -> Path:
        directory = content_paths.language_dir(code)
        write_json(
            directory / "pack.json",
            {
                "code": code,
                "name": code.upper(),
                "locale": f"{code}-{code.upper()}",
                "matchAccentedInitials": match_accents,
                "isPublished": True,
                "audio": audio or {"source": "recording"},
            },
        )
        write_json(directory / "letters.json", {"letters": letters})
        write_json(directory / "ui.json", {"strings": ui if ui is not None else UI_STRINGS})
        return directory

    return write


@pytest.fixture
def french(write_language: LanguageWriter) -> Path:
    return write_language(
        "fr",
        [
            letter("a", [word("ananas", "ananas"), word("abeille", "abeille", "ant")]),
            letter("e", [word("elephant", "éléphant"), word("etoile", "étoile", "ant")]),
            letter("w", []),
        ],
        match_accents=True,
    )
