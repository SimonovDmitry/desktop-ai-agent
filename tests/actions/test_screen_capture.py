import os
import struct
from pathlib import Path

import Quartz

from deskagent.actions.vision import screen


def test_capture_returns_dimensions_and_private_file(monkeypatch):
    monkeypatch.setattr(screen.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(Quartz, "CGPreflightScreenCaptureAccess", lambda: True)

    def fake_run(command, **kwargs):
        Path(command[-1]).write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8 + struct.pack(">II", 20, 10))

    monkeypatch.setattr(screen.subprocess, "run", fake_run)
    result = screen._capture(42)
    try:
        assert result["width"] == 20 and result["height"] == 10
        assert result["window_id"] == 42
        assert os.stat(result["path"]).st_mode & 0o777 == 0o600
    finally:
        Path(result["path"]).unlink(missing_ok=True)
