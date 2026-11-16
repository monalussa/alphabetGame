from dataclasses import dataclass, field
from typing import Literal

AudioSource = Literal["piper", "recording"]


@dataclass(frozen=True)
class AudioConfig:
    source: AudioSource
    voice: str | None = None
    length_scale: float | None = None


@dataclass(frozen=True)
class Word:
    id: str
    text: str
    concept: str
    speech: str | None = None

    @property
    def spoken_text(self) -> str:
        return self.speech or self.text


@dataclass(frozen=True)
class Character:
    name: str
    line: str
    speech: str | None = None

    @property
    def spoken_text(self) -> str:
        return self.speech or self.line


@dataclass(frozen=True)
class Letter:
    id: str
    letter: str
    display: str
    name: str
    keys: tuple[str, ...]
    is_skipped: bool
    character: Character | None
    words: tuple[Word, ...]


@dataclass(frozen=True)
class Language:
    code: str
    name: str
    locale: str
    should_match_accented_initials: bool
    audio: AudioConfig
    letters: tuple[Letter, ...]
    ui_strings: dict[str, str]


@dataclass(frozen=True)
class Concept:
    id: str
    image_id: str | None
    emoji: str | None


@dataclass(frozen=True)
class ImageRecord:
    image_id: str
    file: str
    license: str
    is_reviewed: bool


@dataclass
class Content:
    concepts: dict[str, Concept]
    images: dict[str, ImageRecord]
    languages: dict[str, Language] = field(default_factory=dict)
