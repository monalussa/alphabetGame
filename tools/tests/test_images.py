import json
from pathlib import Path
from unittest.mock import patch

import pytest
from conftest import write_json

from alphabet_tools.images.approval import ApprovalError, approve_images
from alphabet_tools.images.openmoji import fetch_openmoji
from alphabet_tools.images.pending import PendingImage, incoming_dir, read_pending, write_pending
from alphabet_tools.images.svg_safety import UnsafeSvgError, ensure_safe_svg, find_problems
from alphabet_tools.paths import ContentPaths

SAFE_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 72"><circle r="4"/></svg>'


def svg(body: str) -> bytes:
    return f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">{body}</svg>'.encode()


def test_simple_svg_is_safe() -> None:
    assert find_problems(SAFE_SVG) == []


@pytest.mark.parametrize(
    "body",
    [
        "<script>alert(1)</script>",
        '<circle onload="alert(1)"/>',
        '<image href="https://evil.example/x.png"/>',
        '<use xlink:href="https://evil.example/s.svg#a"/>',
        '<rect fill="url(https://evil.example/p)"/>',
        "<style>@import url(https://evil.example/a.css);</style>",
        "<foreignObject><div/></foreignObject>",
        '<a href="javascript:alert(1)"><circle/></a>',
    ],
)
def test_active_or_external_content_is_rejected(body: str) -> None:
    assert find_problems(svg(body)) != []


def test_local_fragment_references_are_allowed() -> None:
    body = '<defs><linearGradient id="g"/></defs><rect fill="url(#g)"/><use href="#g"/>'

    assert find_problems(svg(body)) == []


def test_entity_expansion_is_rejected() -> None:
    bomb = b'<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY a "aaaa">]><svg xmlns="http://www.w3.org/2000/svg">&a;</svg>'

    assert find_problems(bomb) != []


def test_non_svg_root_is_rejected() -> None:
    assert find_problems(b"<html><body/></html>") == ["root element is not <svg>"]


def test_oversized_file_is_rejected() -> None:
    assert "larger than" in find_problems(b" " * 70_000)[0]


def test_ensure_safe_svg_raises_with_file_name(tmp_path: Path) -> None:
    path = tmp_path / "bad.svg"
    path.write_bytes(svg("<script/>"))

    with pytest.raises(UnsafeSvgError, match=r"bad\.svg"):
        ensure_safe_svg(path)


def add_pending(paths: ContentPaths, image_id: str, data: bytes = SAFE_SVG) -> None:
    (incoming_dir(paths)).mkdir(parents=True, exist_ok=True)
    (incoming_dir(paths) / f"{image_id}.svg").write_bytes(data)
    pending = read_pending(paths)
    pending[image_id] = PendingImage(
        imageId=image_id,
        file=f"{image_id}.svg",
        sourceUrl="own-work",
        author="Test",
        license="CC-BY-SA-4.0",
        licenseUrl="https://creativecommons.org/licenses/by-sa/4.0/",
        modified=False,
    )
    write_pending(paths, pending)


def test_approval_moves_file_records_review_and_links_concept(
    content_paths: ContentPaths, french: Path
) -> None:
    add_pending(content_paths, "apple")

    approve_images(content_paths, ["apple"], reviewer="tester")

    manifest = json.loads(content_paths.image_manifest_file.read_text())
    concepts = json.loads(content_paths.concepts_file.read_text())
    assert (content_paths.images_dir / "apple.svg").is_file()
    assert not (incoming_dir(content_paths) / "apple.svg").exists()
    assert manifest["images"][0]["reviewedBy"] == "tester"
    assert concepts["concepts"]["apple"]["imageId"] == "apple"
    assert read_pending(content_paths) == {}


def test_approving_unknown_image_fails(content_paths: ContentPaths) -> None:
    with pytest.raises(ApprovalError, match="not pending"):
        approve_images(content_paths, ["ghost"], reviewer="tester")


def test_unsafe_pending_image_cannot_be_approved(content_paths: ContentPaths) -> None:
    add_pending(content_paths, "apple", svg("<script/>"))

    with pytest.raises(UnsafeSvgError):
        approve_images(content_paths, ["apple"], reviewer="tester")


class FakeResponse:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


def write_sources(paths: ContentPaths, concepts: dict[str, str]) -> None:
    write_json(
        paths.images_dir / "sources" / "openmoji.json", {"revision": "abc", "concepts": concepts}
    )


def test_fetch_downloads_safe_pictures_into_review_area(content_paths: ContentPaths) -> None:
    write_sources(content_paths, {"apple": "1F34E"})

    with patch("urllib.request.urlopen", return_value=FakeResponse(SAFE_SVG)) as urlopen:
        report = fetch_openmoji(content_paths, already_approved=set())

    assert report.downloaded == ["apple"]
    assert urlopen.call_args.args[0].endswith("/abc/color/svg/1F34E.svg")
    assert read_pending(content_paths)["apple"].license == "CC-BY-SA-4.0"


def test_fetch_rejects_unsafe_download_and_keeps_nothing(content_paths: ContentPaths) -> None:
    write_sources(content_paths, {"apple": "1F34E"})

    with patch("urllib.request.urlopen", return_value=FakeResponse(svg("<script/>"))):
        report = fetch_openmoji(content_paths, already_approved=set())

    assert report.rejected and not report.downloaded
    assert not (incoming_dir(content_paths) / "apple.svg").exists()


def test_fetch_refuses_hexcode_that_could_change_the_url(content_paths: ContentPaths) -> None:
    write_sources(content_paths, {"apple": "../../evil"})

    with patch("urllib.request.urlopen") as urlopen:
        report = fetch_openmoji(content_paths, already_approved=set())

    urlopen.assert_not_called()
    assert report.rejected


def test_manifest_image_that_became_unsafe_fails_validation(
    content_paths: ContentPaths, french: Path
) -> None:
    from alphabet_tools.checks import check_content
    from alphabet_tools.loader import load_content

    add_pending(content_paths, "apple")
    approve_images(content_paths, ["apple"], reviewer="tester")
    (content_paths.images_dir / "apple.svg").write_bytes(svg("<script/>"))
    content, issues = load_content(content_paths)

    issues += check_content(content, content_paths)

    assert any("forbidden element <script>" in issue.message for issue in issues)
