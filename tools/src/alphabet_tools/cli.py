"""alphabet-content: validate, build and generate audio for alphabetGame content."""

import argparse
import logging
import sys

from alphabet_tools.checks import check_content
from alphabet_tools.clips import check_audio
from alphabet_tools.issues import Issue, has_errors
from alphabet_tools.loader import load_content
from alphabet_tools.model import Content
from alphabet_tools.paths import DEFAULT_PATHS, ContentPaths

EXIT_OK = 0
EXIT_INVALID = 1


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args(argv)
    return int(args.handler(args, DEFAULT_PATHS))


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="alphabet-content", description=__doc__)
    commands = parser.add_subparsers(required=True)

    validate = commands.add_parser("validate", help="check all content")
    validate.add_argument("--strict", action="store_true", help="missing audio is an error")
    validate.set_defaults(handler=run_validate)

    build = commands.add_parser("build", help="validate, then write runtime packs to public/")
    build.add_argument("--strict", action="store_true")
    build.set_defaults(handler=run_build)

    audio = commands.add_parser("audio", help="generate audio clips for one language")
    audio.add_argument("language", help="language code, e.g. fr")
    audio.add_argument("--force", action="store_true", help="regenerate unchanged clips")
    audio.set_defaults(handler=run_audio)

    record = commands.add_parser("record", help="open a local page to record a language's clips")
    record.add_argument("language", help="language code, e.g. hr")
    record.add_argument("--port", type=int, default=8765)
    record.set_defaults(handler=run_record)

    images = commands.add_parser("images", help="fetch, preview and approve pictures")
    image_commands = images.add_subparsers(required=True)
    fetch = image_commands.add_parser("fetch", help="download OpenMoji pictures to review")
    fetch.set_defaults(handler=run_images_fetch)
    preview = image_commands.add_parser("preview", help="write a contact sheet of pending pictures")
    preview.add_argument("--language", default="fr")
    preview.set_defaults(handler=run_images_preview)
    approve = image_commands.add_parser("approve", help="approve reviewed pictures")
    approve.add_argument("image_ids", nargs="*")
    approve.add_argument("--all", action="store_true", help="approve every pending picture")
    approve.add_argument("--reviewer", required=True)
    approve.set_defaults(handler=run_images_approve)

    fun = commands.add_parser("fun-sounds", help="synthesize the fun sounds")
    fun.set_defaults(handler=run_fun_sounds)
    return parser.parse_args(argv)


def validate_all(paths: ContentPaths, is_strict: bool) -> tuple[Content, list[Issue]]:
    content, issues = load_content(paths)
    issues += check_content(content, paths)
    for language in content.languages.values():
        issues += check_audio(language, paths, is_strict)
    return content, issues


def print_issues(issues: list[Issue]) -> None:
    for issue in sorted(issues, key=lambda issue: (issue.severity, issue.location)):
        print(issue, file=sys.stderr)


def run_validate(args: argparse.Namespace, paths: ContentPaths) -> int:
    content, issues = validate_all(paths, args.strict)
    print_issues(issues)
    if has_errors(issues):
        return EXIT_INVALID
    print(f"content OK: {', '.join(content.languages)}")
    return EXIT_OK


def run_build(args: argparse.Namespace, paths: ContentPaths) -> int:
    from alphabet_tools.pack_builder import build_packs

    content, issues = validate_all(paths, args.strict)
    print_issues(issues)
    if has_errors(issues):
        return EXIT_INVALID
    written = build_packs(content, paths)
    print(f"built {len(written)} pack files into {paths.output_dir}")
    return EXIT_OK


def run_audio(args: argparse.Namespace, paths: ContentPaths) -> int:
    from alphabet_tools.audio_generation import generate_language_audio

    content, issues = load_content(paths)
    issues += check_content(content, paths)
    print_issues(issues)
    language = content.languages.get(args.language)
    if has_errors(issues) or language is None:
        print(f"cannot generate audio for '{args.language}'", file=sys.stderr)
        return EXIT_INVALID
    report = generate_language_audio(language, paths, args.force)
    print(
        f"{language.code}: {report.generated} generated, {report.unchanged} unchanged, "
        f"{report.missing_recordings} recordings missing"
    )
    return EXIT_OK


def run_fun_sounds(_args: argparse.Namespace, paths: ContentPaths) -> int:
    from alphabet_tools.fun_sounds import generate_fun_sounds

    written = generate_fun_sounds(paths.fun_sounds_dir)
    print(f"wrote {len(written)} fun sounds to {paths.fun_sounds_dir}")
    return EXIT_OK


def run_record(args: argparse.Namespace, paths: ContentPaths) -> int:
    from alphabet_tools.recorder.server import serve

    content, issues = load_content(paths)
    issues += check_content(content, paths)
    print_issues(issues)
    language = content.languages.get(args.language)
    if has_errors(issues) or language is None:
        print(f"cannot record for '{args.language}'", file=sys.stderr)
        return EXIT_INVALID
    serve(language, paths, args.port)
    return EXIT_OK


def run_images_fetch(_args: argparse.Namespace, paths: ContentPaths) -> int:
    from alphabet_tools.images.approval import approved_image_ids
    from alphabet_tools.images.openmoji import fetch_openmoji

    report = fetch_openmoji(paths, approved_image_ids(paths))
    for rejection in report.rejected:
        print(f"REJECTED {rejection}", file=sys.stderr)
    print(f"{len(report.downloaded)} downloaded, {len(report.skipped)} already present")
    return EXIT_INVALID if report.rejected else EXIT_OK


def run_images_preview(args: argparse.Namespace, paths: ContentPaths) -> int:
    from alphabet_tools.images.preview import write_preview

    content, _ = load_content(paths)
    print(f"open {write_preview(paths, content, args.language)}")
    return EXIT_OK


def run_images_approve(args: argparse.Namespace, paths: ContentPaths) -> int:
    from alphabet_tools.images.approval import ApprovalError, approve_images
    from alphabet_tools.images.pending import read_pending
    from alphabet_tools.images.svg_safety import UnsafeSvgError

    image_ids = sorted(read_pending(paths)) if args.all else args.image_ids
    if not image_ids:
        print("nothing to approve", file=sys.stderr)
        return EXIT_INVALID
    try:
        approved = approve_images(paths, image_ids, args.reviewer)
    except (ApprovalError, UnsafeSvgError) as exc:
        print(f"approval failed: {exc}", file=sys.stderr)
        return EXIT_INVALID
    print(f"approved {len(approved)} pictures")
    return EXIT_OK
