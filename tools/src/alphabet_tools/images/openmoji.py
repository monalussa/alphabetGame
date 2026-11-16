"""Downloads OpenMoji pictures for concepts at a pinned release into the review area."""

import json
import logging
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from alphabet_tools.images.pending import PendingImage, incoming_dir, read_pending, write_pending
from alphabet_tools.images.svg_safety import UnsafeSvgError, find_problems
from alphabet_tools.paths import ContentPaths

logger = logging.getLogger(__name__)

SOURCES_FILE = "sources/openmoji.json"
RAW_BASE = "https://raw.githubusercontent.com/hfg-gmuend/openmoji"
LIBRARY_BASE = "https://openmoji.org/library/emoji-"
LICENSE = "CC-BY-SA-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
AUTHOR = "OpenMoji (HfG Schwäbisch Gmünd)"
DOWNLOAD_TIMEOUT_SECONDS = 30
HEXCODE_ALPHABET = set("0123456789ABCDEF-")


@dataclass(frozen=True)
class FetchReport:
    downloaded: list[str]
    skipped: list[str]
    rejected: list[str]


def read_sources(paths: ContentPaths) -> tuple[str, dict[str, str]]:
    raw = json.loads((paths.images_dir / SOURCES_FILE).read_text(encoding="utf-8"))
    return raw["revision"], raw["concepts"]


def fetch_openmoji(paths: ContentPaths, already_approved: set[str]) -> FetchReport:
    revision, concepts = read_sources(paths)
    pending = read_pending(paths)
    report = FetchReport([], [], [])
    for concept_id, hexcode in sorted(concepts.items()):
        if concept_id in already_approved or concept_id in pending:
            report.skipped.append(concept_id)
            continue
        try:
            pending[concept_id] = download(paths, revision, concept_id, hexcode)
            report.downloaded.append(concept_id)
        except (UnsafeSvgError, OSError, ValueError) as exc:
            logger.warning("image rejected", extra={"concept": concept_id, "reason": str(exc)})
            report.rejected.append(f"{concept_id}: {exc}")
    write_pending(paths, pending)
    return report


def download(paths: ContentPaths, revision: str, concept_id: str, hexcode: str) -> PendingImage:
    if not hexcode or not set(hexcode) <= HEXCODE_ALPHABET:
        raise ValueError(f"invalid hexcode {hexcode!r}")
    url = f"{RAW_BASE}/{revision}/color/svg/{hexcode}.svg"
    with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:  # noqa: S310 - fixed https base
        data = response.read()
    problems = find_problems(data)
    if problems:
        raise UnsafeSvgError("; ".join(problems))
    file_name = f"{concept_id}.svg"
    target: Path = incoming_dir(paths) / file_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return PendingImage(
        imageId=concept_id,
        file=file_name,
        sourceUrl=f"{LIBRARY_BASE}{hexcode}/",
        author=AUTHOR,
        license=LICENSE,
        licenseUrl=LICENSE_URL,
        modified=False,
    )
