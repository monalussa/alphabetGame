from pathlib import Path

from conftest import LanguageWriter, letter, word, write_json

from alphabet_tools.checks import check_content
from alphabet_tools.issues import Issue
from alphabet_tools.loader import load_content
from alphabet_tools.paths import DEFAULT_PATHS, ContentPaths


def run_checks(paths: ContentPaths) -> list[Issue]:
    content, issues = load_content(paths)
    return issues + check_content(content, paths)


def errors(issues: list[Issue]) -> list[str]:
    return [issue.message for issue in issues if issue.severity == "error"]


def test_valid_content_has_no_errors(content_paths: ContentPaths, french: Path) -> None:
    issues = run_checks(content_paths)

    assert errors(issues) == []


def test_repository_content_has_no_errors() -> None:
    issues = run_checks(DEFAULT_PATHS)

    assert errors(issues) == []


def test_word_starting_with_another_letter_is_an_error(
    content_paths: ContentPaths, write_language: LanguageWriter
) -> None:
    write_language("fr", [letter("a", [word("pomme", "pomme"), word("ananas", "ananas")])])

    issues = run_checks(content_paths)

    assert "word 'pomme' starts with 'nothing', not 'a'" in errors(issues)


def test_french_accented_initial_belongs_to_plain_letter(
    content_paths: ContentPaths, french: Path
) -> None:
    issues = run_checks(content_paths)

    assert not any("éléphant" in message for message in errors(issues))


def test_croatian_accented_letter_is_separate_from_plain_letter(
    content_paths: ContentPaths, write_language: LanguageWriter
) -> None:
    write_language(
        "fr",
        [
            letter("c", [word("casa", "čaša"), word("cipela", "cipela")]),
            letter("ch", [word("carapa", "čarapa"), word("cokolada", "čokolada")], letter="č"),
        ],
    )

    issues = run_checks(content_paths)

    assert errors(issues) == ["word 'čaša' starts with 'č', not 'c'"]


def test_digraph_word_belongs_to_digraph_not_single_letter(
    content_paths: ContentPaths, write_language: LanguageWriter
) -> None:
    write_language(
        "fr",
        [
            letter("d", [word("dzem", "džem"), word("duga", "duga")]),
            letter("dzh", [word("dzep", "džep"), word("dzungla", "džungla")], letter="dž", keys=[]),
        ],
    )

    issues = run_checks(content_paths)

    assert errors(issues) == ["word 'džem' starts with 'dž', not 'd'"]


def test_key_assigned_to_two_letters_is_an_error(
    content_paths: ContentPaths, write_language: LanguageWriter
) -> None:
    write_language(
        "fr",
        [
            letter("a", [word("ananas", "ananas"), word("abeille", "abeille")]),
            letter("b", [word("banane", "banane"), word("bateau", "bateau")], keys=["a"]),
        ],
    )

    issues = run_checks(content_paths)

    assert "key 'a' is assigned to 2 letters" in errors(issues)


def test_unknown_concept_is_an_error(
    content_paths: ContentPaths, write_language: LanguageWriter
) -> None:
    write_language("fr", [letter("a", [word("avion", "avion", "airplane"), word("a2", "ami")])])

    issues = run_checks(content_paths)

    assert "unknown concept 'airplane'" in errors(issues)


def test_duplicate_word_id_is_an_error(
    content_paths: ContentPaths, write_language: LanguageWriter
) -> None:
    write_language("fr", [letter("a", [word("ananas", "ananas"), word("ananas", "abeille")])])

    issues = run_checks(content_paths)

    assert "duplicate word id 'ananas'" in errors(issues)


def test_missing_ui_string_is_an_error(
    content_paths: ContentPaths, french: Path, write_language: LanguageWriter
) -> None:
    write_language(
        "hr",
        [letter("a", [word("auto", "auto"), word("avion", "avion")])],
        ui={"app.title": "Igra"},
    )

    issues = run_checks(content_paths)

    assert "missing string 'start.play'" in errors(issues)


def test_id_with_path_characters_is_rejected_by_schema(
    content_paths: ContentPaths, write_language: LanguageWriter
) -> None:
    write_language("fr", [letter("a", [word("../evil", "ananas"), word("abeille", "abeille")])])

    issues = run_checks(content_paths)

    assert any("does not match" in message for message in errors(issues))


def test_skipped_letter_with_words_is_rejected_by_schema(
    content_paths: ContentPaths, write_language: LanguageWriter
) -> None:
    skipped = letter("a", [word("ananas", "ananas"), word("abeille", "abeille")], skip=True)
    write_language("fr", [skipped])

    issues = run_checks(content_paths)

    assert errors(issues) != []


def test_pack_code_must_match_folder_name(content_paths: ContentPaths, french: Path) -> None:
    write_json(
        french / "pack.json",
        {
            "code": "en",
            "name": "X",
            "locale": "en-US",
            "matchAccentedInitials": False,
            "isPublished": True,
            "audio": {"source": "recording"},
        },
    )

    issues = run_checks(content_paths)

    assert "pack code 'en' must match folder name" in errors(issues)


def test_concept_image_without_review_is_an_error(
    content_paths: ContentPaths, french: Path
) -> None:
    write_json(
        content_paths.concepts_file,
        {"concepts": {"apple": {"imageId": "apple"}, "ant": {"emoji": "🐜"}}},
    )
    record = {
        "imageId": "apple",
        "file": "apple.svg",
        "sourceUrl": "https://example.org/apple",
        "author": "Someone",
        "license": "CC0-1.0",
        "licenseUrl": "https://creativecommons.org/publicdomain/zero/1.0/",
        "modified": False,
        "reviewedBy": None,
        "reviewedAt": None,
    }
    write_json(content_paths.image_manifest_file, {"images": [record]})

    issues = run_checks(content_paths)

    assert "image 'apple' is not license-reviewed" in errors(issues)


def test_letter_with_two_words_is_only_a_warning(content_paths: ContentPaths, french: Path) -> None:
    issues = run_checks(content_paths)

    assert any(issue.severity == "warning" and "only 2 words" in issue.message for issue in issues)


def test_invalid_json_is_reported_not_raised(content_paths: ContentPaths, french: Path) -> None:
    (french / "letters.json").write_text("{ not json", encoding="utf-8")

    issues = run_checks(content_paths)

    assert any("invalid JSON" in message for message in errors(issues))
