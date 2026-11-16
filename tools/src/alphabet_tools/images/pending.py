"""Images waiting for license review live in content/images/_incoming/ with pending.json."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from alphabet_tools.paths import ContentPaths

PENDING_FILE = "pending.json"


@dataclass(frozen=True)
class PendingImage:
    imageId: str  # noqa: N815 - matches the manifest's JSON field names
    file: str
    sourceUrl: str  # noqa: N815
    author: str
    license: str
    licenseUrl: str  # noqa: N815
    modified: bool


def incoming_dir(paths: ContentPaths) -> Path:
    return paths.images_dir / "_incoming"


def read_pending(paths: ContentPaths) -> dict[str, PendingImage]:
    path = incoming_dir(paths) / PENDING_FILE
    if not path.is_file():
        return {}
    records = json.loads(path.read_text(encoding="utf-8"))
    return {record["imageId"]: PendingImage(**record) for record in records}


def write_pending(paths: ContentPaths, pending: dict[str, PendingImage]) -> None:
    path = incoming_dir(paths) / PENDING_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    records = [asdict(record) for _, record in sorted(pending.items())]
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
