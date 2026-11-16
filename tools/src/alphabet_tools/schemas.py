import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from alphabet_tools.issues import Issue, error

SCHEMA_SUFFIX = ".schema.json"


class SchemaSet:
    """All content schemas, with cross-file $refs resolved locally (never over the network)."""

    def __init__(self, schemas_dir: Path) -> None:
        resources = {
            path.name: Resource.from_contents(read_json(path))
            for path in sorted(schemas_dir.glob(f"*{SCHEMA_SUFFIX}"))
        }
        self._registry: Registry[Any] = Registry().with_resources(resources.items())
        self._schemas = {name: resource.contents for name, resource in resources.items()}

    def validate(self, document: Any, schema_name: str, location: str) -> list[Issue]:
        schema = self._schemas.get(schema_name)
        if schema is None:
            return [error(location, f"unknown schema {schema_name}")]
        validator = Draft202012Validator(schema, registry=self._registry)
        return [
            error(f"{location}{format_path(e.absolute_path)}", e.message)
            for e in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
        ]


def format_path(path: Any) -> str:
    parts = "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in path)
    return parts and f" {parts.lstrip('.')}"


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContentFileError(f"{path}: invalid JSON ({exc.msg} at line {exc.lineno})") from exc


class ContentFileError(Exception):
    """A content file is missing or not valid JSON."""
