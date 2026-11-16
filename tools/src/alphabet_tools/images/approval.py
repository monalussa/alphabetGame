"""Moves reviewed images from the review area into the library and links them to concepts."""

import datetime
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from alphabet_tools.images.pending import incoming_dir, read_pending, write_pending
from alphabet_tools.images.svg_safety import ensure_safe_svg
from alphabet_tools.paths import ContentPaths


class ApprovalError(Exception):
    """An image cannot be approved (not pending, or unsafe)."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, document: Any) -> None:
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def approve_images(paths: ContentPaths, image_ids: list[str], reviewer: str) -> list[str]:
    pending = read_pending(paths)
    unknown = sorted(set(image_ids) - set(pending))
    if unknown:
        raise ApprovalError(f"not pending: {', '.join(unknown)}")
    manifest = read_json(paths.image_manifest_file)
    concepts = read_json(paths.concepts_file)
    today = datetime.date.today().isoformat()
    records = {record["imageId"]: record for record in manifest["images"]}

    for image_id in image_ids:
        record = pending.pop(image_id)
        source = incoming_dir(paths) / record.file
        ensure_safe_svg(source)
        source.replace(paths.images_dir / record.file)
        records[image_id] = {**asdict(record), "reviewedBy": reviewer, "reviewedAt": today}
        if image_id in concepts["concepts"]:
            concepts["concepts"][image_id]["imageId"] = image_id

    manifest["images"] = [records[key] for key in sorted(records)]
    write_json(paths.image_manifest_file, manifest)
    write_json(paths.concepts_file, concepts)
    write_pending(paths, pending)
    return image_ids


def approved_image_ids(paths: ContentPaths) -> set[str]:
    return {record["imageId"] for record in read_json(paths.image_manifest_file)["images"]}
