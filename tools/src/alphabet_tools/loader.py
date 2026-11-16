from pathlib import Path
from typing import Any

from alphabet_tools.issues import Issue, error
from alphabet_tools.model import (
    AudioConfig,
    Character,
    Concept,
    Content,
    ImageRecord,
    Language,
    Letter,
    Word,
)
from alphabet_tools.paths import ContentPaths
from alphabet_tools.schemas import ContentFileError, SchemaSet, read_json

TEMPLATE_PREFIX = "_"
LANGUAGE_FILES = {
    "pack.json": "pack.schema.json",
    "letters.json": "letters.schema.json",
    "ui.json": "ui.schema.json",
}


def load_content(paths: ContentPaths) -> tuple[Content, list[Issue]]:
    schemas = SchemaSet(paths.schemas_dir)
    issues: list[Issue] = []

    concepts_doc = load_document(paths.concepts_file, "concepts.schema.json", schemas, issues)
    manifest_doc = load_document(
        paths.image_manifest_file, "image-manifest.schema.json", schemas, issues
    )
    content = Content(
        concepts=parse_concepts(concepts_doc) if concepts_doc is not None else {},
        images=parse_image_manifest(manifest_doc) if manifest_doc is not None else {},
    )

    for language_dir in list_language_dirs(paths.languages_dir):
        language = load_language(language_dir, schemas, issues)
        if language is not None:
            content.languages[language.code] = language
    return content, issues


def list_language_dirs(languages_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in languages_dir.iterdir()
        if path.is_dir() and not path.name.startswith(TEMPLATE_PREFIX)
    )


def load_document(
    path: Path, schema_name: str, schemas: SchemaSet, issues: list[Issue]
) -> Any | None:
    location = str(path)
    if not path.is_file():
        issues.append(error(location, "file is missing"))
        return None
    try:
        document = read_json(path)
    except ContentFileError as exc:
        issues.append(error(location, str(exc)))
        return None
    schema_issues = schemas.validate(document, schema_name, location)
    issues.extend(schema_issues)
    return None if schema_issues else document


def load_language(language_dir: Path, schemas: SchemaSet, issues: list[Issue]) -> Language | None:
    documents = {
        file_name: load_document(language_dir / file_name, schema_name, schemas, issues)
        for file_name, schema_name in LANGUAGE_FILES.items()
    }
    pack, letters, ui = (documents[name] for name in LANGUAGE_FILES)
    if pack is None or letters is None or ui is None:
        return None
    if pack["code"] != language_dir.name:
        issues.append(
            error(str(language_dir), f"pack code '{pack['code']}' must match folder name")
        )
        return None
    return Language(
        code=pack["code"],
        name=pack["name"],
        locale=pack["locale"],
        should_match_accented_initials=pack["matchAccentedInitials"],
        audio=parse_audio_config(pack["audio"]),
        letters=tuple(parse_letter(item) for item in letters["letters"]),
        ui_strings=dict(ui["strings"]),
    )


def parse_audio_config(raw: dict[str, Any]) -> AudioConfig:
    return AudioConfig(
        source=raw["source"], voice=raw.get("voice"), length_scale=raw.get("lengthScale")
    )


def parse_letter(raw: dict[str, Any]) -> Letter:
    character = raw.get("character")
    return Letter(
        id=raw["id"],
        letter=raw["letter"],
        display=raw["display"],
        name=raw["name"],
        keys=tuple(raw["keys"]),
        is_skipped=raw.get("skip", False),
        character=Character(**character) if character else None,
        words=tuple(Word(**word) for word in raw.get("words", [])),
    )


def parse_concepts(raw: dict[str, Any]) -> dict[str, Concept]:
    return {
        concept_id: Concept(id=concept_id, image_id=value.get("imageId"), emoji=value.get("emoji"))
        for concept_id, value in raw["concepts"].items()
    }


def parse_image_manifest(raw: dict[str, Any]) -> dict[str, ImageRecord]:
    return {
        record["imageId"]: ImageRecord(
            image_id=record["imageId"],
            file=record["file"],
            license=record["license"],
            is_reviewed=bool(record["reviewedBy"] and record["reviewedAt"]),
        )
        for record in raw["images"]
    }
