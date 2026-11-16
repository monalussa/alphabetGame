import unicodedata
from collections import Counter

from alphabet_tools.issues import Issue, error, warning
from alphabet_tools.model import Content, Language, Letter
from alphabet_tools.paths import ContentPaths

REFERENCE_LANGUAGE = "fr"
PREFERRED_WORD_COUNT = 3


def check_content(content: Content, paths: ContentPaths) -> list[Issue]:
    issues: list[Issue] = []
    for language in content.languages.values():
        issues += check_unique_ids(language)
        issues += check_keys(language)
        issues += check_word_initials(language)
        issues += check_word_counts(language)
        issues += check_concept_references(language, content)
    issues += check_ui_keys(content)
    issues += check_concepts(content, paths)
    return issues


def check_unique_ids(language: Language) -> list[Issue]:
    location = f"{language.code}/letters.json"
    letter_ids = [letter.id for letter in language.letters]
    letters = [letter.letter for letter in language.letters]
    word_ids = [word.id for letter in language.letters for word in letter.words]
    return [
        error(location, f"duplicate {kind} '{value}'")
        for kind, values in (("letter id", letter_ids), ("letter", letters), ("word id", word_ids))
        for value, count in Counter(values).items()
        if count > 1
    ]


def check_keys(language: Language) -> list[Issue]:
    location = f"{language.code}/letters.json"
    issues: list[Issue] = []
    key_counts = Counter(key for letter in language.letters for key in letter.keys)
    for key, count in key_counts.items():
        if count > 1:
            issues.append(error(location, f"key '{key}' is assigned to {count} letters"))
    for key in key_counts:
        if key != key.lower():
            issues.append(error(location, f"key '{key}' must be lowercase"))
    return issues


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def normalize_initial(text: str, should_strip_accents: bool) -> str:
    normalized = unicodedata.normalize("NFC", text.casefold())
    return strip_accents(normalized) if should_strip_accents else normalized


def find_initial_letter(text: str, language: Language) -> Letter | None:
    """The longest alphabet letter that starts the word (so 'džem' is DŽ, not D)."""
    should_strip = language.should_match_accented_initials
    word = normalize_initial(text, should_strip)
    candidates = [
        letter
        for letter in language.letters
        if word.startswith(normalize_initial(letter.letter, should_strip))
    ]
    return max(candidates, key=lambda letter: len(letter.letter), default=None)


def check_word_initials(language: Language) -> list[Issue]:
    issues: list[Issue] = []
    for letter in language.letters:
        for word in letter.words:
            initial = find_initial_letter(word.text, language)
            if initial is None or initial.id != letter.id:
                found = initial.letter if initial else "nothing"
                issues.append(
                    error(
                        f"{language.code}/letters.json {letter.id}",
                        f"word '{word.text}' starts with '{found}', not '{letter.letter}'",
                    )
                )
    return issues


def check_word_counts(language: Language) -> list[Issue]:
    return [
        warning(
            f"{language.code}/letters.json {letter.id}",
            f"only {len(letter.words)} words (preferred {PREFERRED_WORD_COUNT})",
        )
        for letter in language.letters
        if not letter.is_skipped and len(letter.words) < PREFERRED_WORD_COUNT
    ]


def check_concept_references(language: Language, content: Content) -> list[Issue]:
    return [
        error(f"{language.code}/letters.json {letter.id}", f"unknown concept '{word.concept}'")
        for letter in language.letters
        for word in letter.words
        if word.concept not in content.concepts
    ]


def check_ui_keys(content: Content) -> list[Issue]:
    reference = content.languages.get(REFERENCE_LANGUAGE)
    if reference is None:
        return [error("languages", f"reference language '{REFERENCE_LANGUAGE}' is missing")]
    expected = set(reference.ui_strings)
    issues: list[Issue] = []
    for language in content.languages.values():
        location = f"{language.code}/ui.json"
        actual = set(language.ui_strings)
        issues += [error(location, f"missing string '{key}'") for key in sorted(expected - actual)]
        issues += [warning(location, f"extra string '{key}'") for key in sorted(actual - expected)]
        issues += [
            error(location, f"empty string '{key}'")
            for key, value in language.ui_strings.items()
            if not value.strip()
        ]
    return issues


def check_concepts(content: Content, paths: ContentPaths) -> list[Issue]:
    used = {
        word.concept
        for language in content.languages.values()
        for letter in language.letters
        for word in letter.words
    }
    issues = [
        warning("concepts.json", f"concept '{concept_id}' is not used by any language")
        for concept_id in sorted(set(content.concepts) - used)
    ]
    for concept in content.concepts.values():
        if concept.image_id is None:
            continue
        record = content.images.get(concept.image_id)
        location = f"concepts.json {concept.id}"
        if record is None:
            issues.append(error(location, f"image '{concept.image_id}' has no manifest record"))
        elif not record.is_reviewed:
            issues.append(error(location, f"image '{concept.image_id}' is not license-reviewed"))
        elif not (paths.images_dir / record.file).is_file():
            issues.append(error(location, f"image file '{record.file}' is missing"))
    return issues
