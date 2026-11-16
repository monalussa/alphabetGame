"""Downloads Piper voice models at a pinned revision and verifies them by SHA-256."""

import hashlib
import json
import logging
import shutil
import tempfile
import urllib.request
from pathlib import Path

from alphabet_tools.paths import REPO_ROOT

logger = logging.getLogger(__name__)

VOICES_LOCK_FILE = REPO_ROOT / "tools" / "voices.lock.json"
VOICES_CACHE_DIR = REPO_ROOT / "tools" / ".cache" / "voices"
DOWNLOAD_TIMEOUT_SECONDS = 120
CHUNK_BYTES = 1 << 20
ALLOWED_URL_PREFIX = "https://huggingface.co/rhasspy/piper-voices/resolve/"


class VoiceError(Exception):
    """A voice is not pinned, cannot be downloaded, or fails verification."""


def ensure_voice(voice: str) -> Path:
    lock = json.loads(VOICES_LOCK_FILE.read_text(encoding="utf-8"))
    entry = lock["voices"].get(voice)
    if entry is None:
        raise VoiceError(f"voice '{voice}' is not pinned in {VOICES_LOCK_FILE.name}")
    for suffix, digest in (("onnx", entry["onnxSha256"]), ("onnx.json", entry["configSha256"])):
        url = f"{lock['baseUrl']}{lock['revision']}/{entry['path']}.{suffix}"
        ensure_file(url, VOICES_CACHE_DIR / f"{voice}.{suffix}", digest)
    return VOICES_CACHE_DIR / f"{voice}.onnx"


def ensure_file(url: str, target: Path, expected_sha256: str) -> None:
    if target.is_file() and sha256_of(target) == expected_sha256:
        return
    if not url.startswith(ALLOWED_URL_PREFIX):
        raise VoiceError(f"refusing to download from unexpected URL {url}")
    target.parent.mkdir(parents=True, exist_ok=True)
    logger.info("downloading voice file", extra={"url": url})
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:  # noqa: S310 - https prefix checked above
                shutil.copyfileobj(response, temporary, CHUNK_BYTES)
        except OSError as exc:
            temporary_path.unlink(missing_ok=True)
            raise VoiceError(f"download failed for {url}") from exc
    actual = sha256_of(temporary_path)
    if actual != expected_sha256:
        temporary_path.unlink(missing_ok=True)
        raise VoiceError(f"checksum mismatch for {url}: got {actual}")
    temporary_path.replace(target)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()
