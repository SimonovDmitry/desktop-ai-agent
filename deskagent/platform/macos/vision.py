from __future__ import annotations

import hashlib
import os
import platform
import struct
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from deskagent.platform.base.vision import VisionService


def _capture(window_id: int | None = None) -> dict:
    if platform.system() != "Darwin":
        raise RuntimeError("Screen capture is supported only on macOS")
    from Quartz import CGPreflightScreenCaptureAccess

    if not CGPreflightScreenCaptureAccess():
        raise PermissionError("Screen Recording permission is required")
    fd, name = tempfile.mkstemp(prefix="deskagent-screen-", suffix=".png")
    os.close(fd)
    path = Path(name)
    command = ["/usr/sbin/screencapture", "-x", "-t", "png"]
    if window_id is not None:
        command += ["-l", str(window_id)]
    try:
        subprocess.run([*command, str(path)], check=True, capture_output=True, timeout=20)
        with path.open("rb") as image:
            header = image.read(24)
        if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
            raise RuntimeError("Screen capture did not produce a PNG image")
        width, height = struct.unpack(">II", header[16:24])
        if width < 1 or height < 1:
            raise RuntimeError("Screen capture is empty")
        path.chmod(0o600)
        return {
            "path": str(path), "width": width, "height": height,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "captured_at": datetime.now(UTC).isoformat(), "window_id": window_id,
        }
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _ocr(path: str) -> list[dict]:
    if platform.system() != "Darwin":
        raise RuntimeError("Text recognition is supported only on macOS")
    try:
        from Foundation import NSURL
        from Vision import VNImageRequestHandler, VNRecognizeTextRequest
    except ImportError as exc:
        raise RuntimeError("Install pyobjc-framework-Vision to read screen text") from exc
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("OCR image exceeds the 50 MB limit")
    with source.open("rb") as image:
        header = image.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("OCR requires a PNG capture")
    width, height = struct.unpack(">II", header[16:24])
    request = VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(1)
    if hasattr(request, "setAutomaticallyDetectsLanguage_"):
        request.setAutomaticallyDetectsLanguage_(True)
    handler = VNImageRequestHandler.alloc().initWithURL_options_(NSURL.fileURLWithPath_(str(source)), {})
    success, error = handler.performRequests_error_([request], None)
    if not success:
        raise RuntimeError(str(error or "Vision OCR failed"))
    lines = []
    for observation in request.results() or []:
        candidates = observation.topCandidates_(1)
        if not candidates:
            continue
        rect = observation.boundingBox()
        lines.append({
            "text": str(candidates[0].string()), "confidence": float(candidates[0].confidence()),
            "bounds": {
                "x": round(rect.origin.x * width),
                "y": round((1 - rect.origin.y - rect.size.height) * height),
                "width": round(rect.size.width * width), "height": round(rect.size.height * height),
            },
        })
    return lines


class MacOSVisionService(VisionService):
    def capture(self, window_id=None):
        return _capture(window_id)

    def read_text(self, path):
        return _ocr(path)
