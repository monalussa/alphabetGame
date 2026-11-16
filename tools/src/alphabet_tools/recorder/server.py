"""Local-only web page for recording a language's clips with the microphone.

Security: binds to 127.0.0.1, checks the Host header (DNS rebinding), requires a per-run
token on every write (CSRF), accepts only known clip ids, size-limited, valid 16-bit WAV.
"""

import json
import logging
import secrets
import tempfile
import wave
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from alphabet_tools.clips import list_clips
from alphabet_tools.model import Language
from alphabet_tools.paths import ContentPaths

logger = logging.getLogger(__name__)

LOOPBACK_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
TOKEN_HEADER = "X-Recorder-Token"  # noqa: S105 - header name, not a secret
TOKEN_PLACEHOLDER = "__RECORDER_TOKEN__"  # noqa: S105 - template marker
RECORDING_PREFIX = "/api/recordings/"
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/recorder.js": ("recorder.js", "text/javascript; charset=utf-8"),
    "/worklet.js": ("worklet.js", "text/javascript; charset=utf-8"),
    "/recorder.css": ("recorder.css", "text/css; charset=utf-8"),
}
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; media-src 'self' blob:; "
        "connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'; "
        "frame-ancestors 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


class RecorderState:
    def __init__(self, language: Language, paths: ContentPaths) -> None:
        self.language = language
        self.recordings_dir = paths.recordings_dir(language.code)
        self.clips = {clip.clip_id: clip.text for clip in list_clips(language)}
        self.token = secrets.token_urlsafe(32)
        self.allowed_hosts: set[str] = set()

    def allow_port(self, port: int) -> None:
        self.allowed_hosts = {f"{LOOPBACK_HOST}:{port}", f"localhost:{port}"}

    def recorded_ids(self) -> list[str]:
        return [
            clip_id for clip_id in self.clips if (self.recordings_dir / f"{clip_id}.wav").is_file()
        ]


class InvalidRecordingError(Exception):
    """Uploaded bytes are not an acceptable WAV file."""


def validate_wav(data: bytes) -> None:
    try:
        with wave.open(BytesIO(data), "rb") as wav:
            is_valid = wav.getsampwidth() == 2 and wav.getnchannels() == 1 and wav.getnframes() > 0
    except (wave.Error, EOFError) as exc:
        raise InvalidRecordingError("not a WAV file") from exc
    if not is_valid:
        raise InvalidRecordingError("expected non-empty 16-bit mono WAV")


def save_atomically(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False, suffix=".part") as temporary:
        temporary.write(data)
    Path(temporary.name).replace(target)


def make_handler(state: RecorderState) -> type[BaseHTTPRequestHandler]:
    class RecorderHandler(BaseHTTPRequestHandler):
        server_version = "alphabet-recorder"
        sys_version = ""

        def log_message(self, format: str, *args: Any) -> None:
            logger.info("request %s", format % args)

        def is_trusted_host(self) -> bool:
            return self.headers.get("Host", "") in state.allowed_hosts

        def send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
            self.send_response(status)
            for name, value in SECURITY_HEADERS.items():
                self.send_header(name, value)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, status: HTTPStatus, document: Any) -> None:
            body = json.dumps(document, ensure_ascii=False).encode("utf-8")
            self.send(status, body, "application/json; charset=utf-8")

        def do_GET(self) -> None:
            if not self.is_trusted_host():
                return self.send_json(HTTPStatus.FORBIDDEN, {"error": "forbidden host"})
            path = urlsplit(self.path).path
            if path == "/api/clips":
                return self.send_clips()
            static = STATIC_FILES.get(path)
            if static is None:
                return self.send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            file_name, content_type = static
            text = files(__package__).joinpath("static", file_name).read_text(encoding="utf-8")
            body = text.replace(TOKEN_PLACEHOLDER, state.token).encode("utf-8")
            return self.send(HTTPStatus.OK, body, content_type)

        def send_clips(self) -> None:
            recorded = set(state.recorded_ids())
            clips = [
                {"id": clip_id, "text": text, "isRecorded": clip_id in recorded}
                for clip_id, text in state.clips.items()
            ]
            self.send_json(HTTPStatus.OK, {"language": state.language.name, "clips": clips})

        def do_PUT(self) -> None:
            rejection = self.check_upload_request()
            if rejection is not None:
                return self.send_json(rejection, {"error": rejection.phrase})
            clip_id = urlsplit(self.path).path.removeprefix(RECORDING_PREFIX)
            data = self.rfile.read(int(self.headers["Content-Length"]))
            try:
                validate_wav(data)
            except InvalidRecordingError as exc:
                return self.send_json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": str(exc)})
            save_atomically(state.recordings_dir / f"{clip_id}.wav", data)
            logger.info("recording saved", extra={"clip_id": clip_id})
            return self.send_json(HTTPStatus.OK, {"id": clip_id, "isRecorded": True})

        def check_upload_request(self) -> HTTPStatus | None:
            path = urlsplit(self.path).path
            clip_id = path.removeprefix(RECORDING_PREFIX)
            length = self.headers.get("Content-Length", "")
            if not self.is_trusted_host():
                return HTTPStatus.FORBIDDEN
            if not secrets.compare_digest(self.headers.get(TOKEN_HEADER, ""), state.token):
                return HTTPStatus.FORBIDDEN
            if not path.startswith(RECORDING_PREFIX) or clip_id not in state.clips:
                return HTTPStatus.NOT_FOUND
            if self.headers.get("Content-Type") != "audio/wav":
                return HTTPStatus.UNSUPPORTED_MEDIA_TYPE
            if not length.isdigit() or not 0 < int(length) <= MAX_UPLOAD_BYTES:
                return HTTPStatus.REQUEST_ENTITY_TOO_LARGE
            return None

    return RecorderHandler


def create_server(language: Language, paths: ContentPaths, port: int) -> ThreadingHTTPServer:
    state = RecorderState(language, paths)
    server = ThreadingHTTPServer((LOOPBACK_HOST, port), make_handler(state))
    state.allow_port(server.server_address[1])
    return server


def serve(language: Language, paths: ContentPaths, port: int = DEFAULT_PORT) -> None:
    server = create_server(language, paths, port)
    print(f"Recorder for {language.name}: open http://{LOOPBACK_HOST}:{port}/  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        server.server_close()
