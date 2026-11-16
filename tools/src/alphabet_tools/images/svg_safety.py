"""Rejects SVG files that could run code or load anything from outside the site."""

import re
from pathlib import Path
from xml.etree.ElementTree import Element

from defusedxml import DefusedXmlException
from defusedxml.ElementTree import ParseError, fromstring

MAX_SVG_BYTES = 64 * 1024
SVG_NAMESPACE = "{http://www.w3.org/2000/svg}"
FORBIDDEN_ELEMENTS = {
    "script",
    "foreignobject",
    "iframe",
    "embed",
    "object",
    "image",
    "audio",
    "video",
    "a",
}
HREF_ATTRIBUTES = {"href", "{http://www.w3.org/1999/xlink}href"}
EXTERNAL_REFERENCE = re.compile(r"url\(\s*['\"]?(?!#)|@import|javascript:|data:", re.IGNORECASE)


class UnsafeSvgError(Exception):
    """The SVG is malformed, too large, or contains active or external content."""


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def check_element(element: Element) -> list[str]:
    problems: list[str] = []
    name = local_name(element.tag)
    if name in FORBIDDEN_ELEMENTS:
        problems.append(f"forbidden element <{name}>")
    for attribute, value in element.attrib.items():
        attribute_name = local_name(attribute)
        if attribute_name.startswith("on"):
            problems.append(f"event handler attribute {attribute_name}")
        if attribute in HREF_ATTRIBUTES and not value.startswith("#"):
            problems.append(f"external reference {value[:60]}")
        if EXTERNAL_REFERENCE.search(value):
            problems.append(f"external or active value in {attribute_name}")
    if name == "style" and element.text and EXTERNAL_REFERENCE.search(element.text):
        problems.append("external or active value in <style>")
    return problems


def find_problems(data: bytes) -> list[str]:
    if len(data) > MAX_SVG_BYTES:
        return [f"larger than {MAX_SVG_BYTES} bytes"]
    try:
        root = fromstring(data, forbid_dtd=True)
    except (ParseError, DefusedXmlException) as exc:
        return [f"not a safe XML document: {exc}"]
    if root.tag != f"{SVG_NAMESPACE}svg":
        return ["root element is not <svg>"]
    return [problem for element in root.iter() for problem in check_element(element)]


def ensure_safe_svg(path: Path) -> None:
    problems = find_problems(path.read_bytes())
    if problems:
        raise UnsafeSvgError(f"{path.name}: {'; '.join(sorted(set(problems)))}")
