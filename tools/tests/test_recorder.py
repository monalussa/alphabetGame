import http.client
import threading
from collections.abc import Iterator
from http.server import ThreadingHTTPServer
from pathlib import Path

import numpy as np
import pytest
from test_audio import tone, write_wav

from alphabet_tools.loader import load_content
from alphabet_tools.paths import ContentPaths
from alphabet_tools.recorder.server import TOKEN_HEADER, create_server


@pytest.fixture
def server(content_paths: ContentPaths, french: Path) -> Iterator[ThreadingHTTPServer]:
    language = load_content(content_paths)[0].languages["fr"]
    running = create_server(language, content_paths, port=0)
    thread = threading.Thread(target=running.serve_forever, daemon=True)
    thread.start()
    yield running
    running.shutdown()
    running.server_close()


def request(
    server: ThreadingHTTPServer,
    method: str,
    path: str,
    *,
    body: bytes = b"",
    headers: dict[str, str] | None = None,
    host: str | None = None,
) -> tuple[int, bytes]:
    port = server.server_address[1]
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.putrequest(method, path, skip_host=True)
    connection.putheader("Host", host or f"127.0.0.1:{port}")
    for name, value in (headers or {}).items():
        connection.putheader(name, value)
    connection.putheader("Content-Length", str(len(body)))
    connection.endheaders(body)
    response = connection.getresponse()
    result = response.status, response.read()
    connection.close()
    return result


def page_token(server: ThreadingHTTPServer) -> str:
    _, page = request(server, "GET", "/")
    marker = b'name="recorder-token" content="'
    start = page.index(marker) + len(marker)
    return page[start : page.index(b'"', start)].decode()


def wav_bytes(tmp_path: Path) -> bytes:
    path = tmp_path / "upload.wav"
    write_wav(path, tone(0.3))
    return path.read_bytes()


def upload_headers(token: str) -> dict[str, str]:
    return {"Content-Type": "audio/wav", TOKEN_HEADER: token}


def test_page_is_served_with_a_fresh_token(server: ThreadingHTTPServer) -> None:
    token = page_token(server)

    assert len(token) >= 32
    assert "__RECORDER_TOKEN__" not in token


def test_foreign_host_header_is_rejected(server: ThreadingHTTPServer) -> None:
    status, _ = request(server, "GET", "/", host="evil.example:80")

    assert status == 403


def test_upload_without_token_is_rejected(server: ThreadingHTTPServer, tmp_path: Path) -> None:
    status, _ = request(
        server,
        "PUT",
        "/api/recordings/word_ananas",
        body=wav_bytes(tmp_path),
        headers={"Content-Type": "audio/wav"},
    )

    assert status == 403


@pytest.mark.parametrize("clip_id", ["word_unknown", "..%2F..%2Fpack", "../../pack"])
def test_upload_for_unknown_or_traversal_id_is_rejected(
    server: ThreadingHTTPServer, tmp_path: Path, clip_id: str
) -> None:
    status, _ = request(
        server,
        "PUT",
        f"/api/recordings/{clip_id}",
        body=wav_bytes(tmp_path),
        headers=upload_headers(page_token(server)),
    )

    assert status == 404


def test_upload_that_is_not_wav_is_rejected(server: ThreadingHTTPServer) -> None:
    status, _ = request(
        server,
        "PUT",
        "/api/recordings/word_ananas",
        body=b"<script>alert(1)</script>",
        headers=upload_headers(page_token(server)),
    )

    assert status == 422


def test_valid_upload_is_saved_as_recording(
    server: ThreadingHTTPServer, tmp_path: Path, content_paths: ContentPaths
) -> None:
    data = wav_bytes(tmp_path)

    status, _ = request(
        server,
        "PUT",
        "/api/recordings/word_ananas",
        body=data,
        headers=upload_headers(page_token(server)),
    )

    saved = content_paths.recordings_dir("fr") / "word_ananas.wav"
    assert status == 200
    assert saved.read_bytes() == data
    assert np.frombuffer(data[44:], dtype="<i2").size > 0
