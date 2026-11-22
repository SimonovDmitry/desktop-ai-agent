"""Service injection and import boundaries must hold without native OS access."""
import ast
import importlib
import struct
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from deskagent.actions.audio import _wav
from deskagent.actions.code import _common as code
from deskagent.actions.code.project import RunProjectTests
from deskagent.actions.documents import _common as documents
from deskagent.actions.productivity import _common as productivity
from deskagent.actions.vision import ocr_inspection
from deskagent.core.services import ServicesFactory
from deskagent.platform.base.code import CodeService
from deskagent.platform.base.documents import DocumentService
from deskagent.platform.base.productivity import ProductivityService
from deskagent.platform.base.wav import WavService
from deskagent.platform.macos.accessibility import MacOSAccessibilityService
from deskagent.platform.macos.browser.manager import BrowserManager


def test_factory_wires_portable_and_native_services(monkeypatch):
    monkeypatch.setattr(ServicesFactory, "get_platform", lambda: "macos")
    services = ServicesFactory.create()
    for field, contract in (("code", CodeService), ("documents", DocumentService),
                            ("productivity", ProductivityService), ("wav", WavService),
                            ("accessibility", MacOSAccessibilityService), ("browser", BrowserManager)):
        assert isinstance(getattr(services, field), contract)
    assert services.accessibility.backend is None  # Factory must not access native AX APIs.


@pytest.mark.parametrize("field,module,method,args", [
    ("code", code, "read_source", (Path("project"), "source.py")),
    ("documents", documents, "read_text", ("notes.txt",)),
    ("productivity", productivity, "with_session", ("session-id", lambda *_: None)),
    ("wav", _wav, "read_wav", ("sample.wav",)),
])
def test_portable_actions_use_injected_services(field, module, method, args):
    operation = Mock(return_value=object())
    context = SimpleNamespace(services=SimpleNamespace(**{field: SimpleNamespace(**{method: operation})}))
    result = getattr(module, method)(context, *args)
    assert result is operation.return_value
    operation.assert_called_once_with(context, *args)


def test_project_test_runner_uses_injected_service():
    operation = Mock(return_value={"run_id": "test", "passed": True})
    context = SimpleNamespace(services=SimpleNamespace(code=SimpleNamespace(run_project_tests=operation)))
    parameters = {"directory": "/project"}
    result = RunProjectTests().execute(context, parameters)
    assert result.success and result.data["passed"]
    operation.assert_called_once_with(context, parameters)


@pytest.mark.parametrize("fail", [False, True])
def test_extended_ocr_uses_vision_service_and_removes_capture(tmp_path, fail):
    capture = tmp_path / "capture.png"
    capture.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\0" * 8 + struct.pack(">II", 4, 3))
    lines = [{"text": "Save", "confidence": 1.0, "bounds": {"x": 0, "y": 0, "width": 2, "height": 1}}]
    vision = SimpleNamespace(
        capture=Mock(return_value={"path": str(capture)}),
        read_text=Mock(return_value=lines, side_effect=RuntimeError("OCR failed") if fail else None),
    )
    context = SimpleNamespace(services=SimpleNamespace(vision=vision))
    result = ocr_inspection.GetImageTextSummary().execute(context, {})
    assert result.success is not fail
    if not fail:
        assert result.data["line_count"] == 1
    vision.capture.assert_called_once_with()
    vision.read_text.assert_called_once_with(str(capture))
    assert not capture.exists()


@pytest.mark.parametrize("legacy,native", [
    ("deskagent.actions.browser.manager", "deskagent.platform.macos.browser.manager"),
    ("deskagent.actions.browser.cdp", "deskagent.platform.common.browser.cdp"),
    ("deskagent.perception.accessibility.client", "deskagent.platform.common.accessibility.client"),
])
def test_compatibility_imports_share_module_identity(legacy, native):
    assert importlib.import_module(legacy) is importlib.import_module(native)


@pytest.mark.parametrize("module", [
    "deskagent.core.services", "deskagent.platform.macos.accessibility_backend",
    "deskagent.actions.browser", "deskagent.perception.accessibility",
])
def test_services_import_in_fresh_process(module):
    subprocess.run([sys.executable, "-c", f"import {module}"], check=True, capture_output=True, timeout=20)


def test_platform_does_not_depend_on_actions_or_perception():
    root = Path(__file__).resolve().parents[2] / "deskagent" / "platform"
    for path in root.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            modules = ([node.module or ""] if isinstance(node, ast.ImportFrom) else
                       [alias.name for alias in node.names] if isinstance(node, ast.Import) else [])
            assert not any(name.startswith(("deskagent.actions", "deskagent.perception")) for name in modules), path


def test_browser_adapter_launches_chromium_with_private_profile(tmp_path, monkeypatch):
    from deskagent.platform.macos.browser import manager as native
    from deskagent.platform.common.browser.models import BrowserInfo, BrowserKind

    service = native.BrowserManager()
    service.profile_root = tmp_path / "profiles"
    info = BrowserInfo("chrome", "Google Chrome", BrowserKind.CHROME, "/unused", True, False, None, 9222)
    monkeypatch.setattr(service, "_browser_info", lambda *_: info)
    monkeypatch.setattr(service, "_backend", lambda *_, **kwargs: object())
    monkeypatch.setattr(service, "_backend_name", lambda *_: "cdp")
    run = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(native.subprocess, "run", run)
    result = service.launch("chrome", "about:blank", incognito=True)
    command = run.call_args.args[0]
    assert result["launched"]
    assert command[:4] == ["open", "-n", "-a", "Google Chrome"]
    assert f"--user-data-dir={service.profile_root / 'chrome'}" in command
    assert "--remote-debugging-port=9222" in command
    assert "--incognito" in command
    assert "about:blank" in command


def test_browser_adapter_blocks_unsafe_url_before_launch(tmp_path, monkeypatch):
    from deskagent.platform.macos.browser import manager as native
    from deskagent.platform.common.browser.models import BrowserInfo, BrowserKind, BrowserSecurityError

    service = native.BrowserManager()
    service.profile_root = tmp_path
    info = BrowserInfo("chrome", "Google Chrome", BrowserKind.CHROME, "/unused", True, False, None, 9222)
    monkeypatch.setattr(service, "_browser_info", lambda *_: info)
    run = Mock()
    monkeypatch.setattr(native.subprocess, "run", run)
    with pytest.raises(BrowserSecurityError):
        service.launch("chrome", "file:///etc/passwd")
    run.assert_not_called()
