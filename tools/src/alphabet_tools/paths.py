from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ContentPaths:
    """Locations of content sources and build output; tests point this at a temp dir."""

    content_dir: Path
    output_dir: Path

    @property
    def schemas_dir(self) -> Path:
        return self.content_dir / "schemas"

    @property
    def languages_dir(self) -> Path:
        return self.content_dir / "languages"

    @property
    def concepts_file(self) -> Path:
        return self.content_dir / "concepts" / "concepts.json"

    @property
    def image_manifest_file(self) -> Path:
        return self.content_dir / "images" / "manifest.json"

    @property
    def images_dir(self) -> Path:
        return self.content_dir / "images"

    @property
    def fun_sounds_dir(self) -> Path:
        return self.content_dir / "sounds" / "fun"

    def language_dir(self, code: str) -> Path:
        return self.languages_dir / code

    def audio_dir(self, code: str) -> Path:
        return self.language_dir(code) / "audio"

    def audio_manifest_file(self, code: str) -> Path:
        return self.language_dir(code) / "audio-manifest.json"

    def recordings_dir(self, code: str) -> Path:
        return self.language_dir(code) / "recordings"

    def characters_dir(self, code: str) -> Path:
        return self.language_dir(code) / "characters"


DEFAULT_PATHS = ContentPaths(
    content_dir=REPO_ROOT / "content",
    output_dir=REPO_ROOT / "public",
)
