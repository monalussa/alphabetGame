"""Contact sheet of pending images, opened locally by the owner before approving."""

import html
from pathlib import Path

from alphabet_tools.images.pending import incoming_dir, read_pending
from alphabet_tools.model import Content
from alphabet_tools.paths import ContentPaths

PREVIEW_FILE = "preview.html"
STYLE = """
body{font-family:system-ui;background:#fff8e7;color:#2b2b2b;margin:24px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
figure{background:#fff;border-radius:12px;margin:0;padding:10px;text-align:center}
img{width:110px;height:110px}figcaption{font-weight:600;font-size:18px}
small{display:block;color:#777;font-weight:400;font-size:12px}
"""


def words_by_concept(content: Content, language_code: str) -> dict[str, list[str]]:
    words: dict[str, list[str]] = {}
    language = content.languages.get(language_code)
    if language is None:
        return words
    for letter in language.letters:
        for word in letter.words:
            words.setdefault(word.concept, []).append(word.text)
    return words


def write_preview(paths: ContentPaths, content: Content, language_code: str) -> Path:
    labels = words_by_concept(content, language_code)
    figures = []
    for image_id, record in sorted(read_pending(paths).items()):
        label = ", ".join(labels.get(image_id, [image_id]))
        figures.append(
            f'<figure><img src="{html.escape(record.file)}" alt="">'
            f"<figcaption>{html.escape(label)}<small>{html.escape(image_id)} · "
            f"{html.escape(record.license)}</small></figcaption></figure>"
        )
    document = (
        '<!doctype html><html><meta charset="utf-8"><title>Pending images</title>'
        f"<style>{STYLE}</style><body><h1>Pending images ({len(figures)})</h1>"
        f'<div class="grid">{"".join(figures)}</div></body></html>'
    )
    target = incoming_dir(paths) / PREVIEW_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(document, encoding="utf-8")
    return target
