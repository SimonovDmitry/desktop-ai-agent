from __future__ import annotations

from pathlib import Path

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult
from deskagent.platform.macos.vision import _capture, _ocr, platform, subprocess  # noqa: F401


class CaptureScreen(Action):
    name = "capture_screen"
    description = "Capture the current screen to a private temporary PNG and return its dimensions"
    category = ActionCategory.SYSTEM
    required_permissions = ("screen_recording",)
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            service = getattr(getattr(context, "services", None), "vision", None)
            return ActionResult(True, service.capture() if service else _capture())
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="SCREEN_CAPTURE_ERROR")


class CaptureWindow(Action):
    name = "capture_window"
    description = "Capture a macOS window by window id to a private temporary PNG"
    category = ActionCategory.SYSTEM
    required_permissions = ("screen_recording",)
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        try:
            service = getattr(getattr(context, "services", None), "vision", None)
            return ActionResult(True, service.capture(parameters["window_id"]) if service
                                else _capture(parameters["window_id"]))
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="SCREEN_CAPTURE_ERROR")


class ReadScreenText(Action):
    name = "read_screen_text"
    description = "Recognize text and screen coordinates in a PNG capture or the current screen"
    category = ActionCategory.SYSTEM
    required_permissions = ()
    parameters_schema = {"path": {"type": "string", "required": False}}

    def execute(self, context, parameters):
        temporary = None
        try:
            service = getattr(getattr(context, "services", None), "vision", None)
            path = (parameters or {}).get("path")
            if not path:
                temporary = service.capture() if service else _capture()
                path = temporary["path"]
            lines = service.read_text(path) if service else _ocr(path)
            return ActionResult(True, {
                "path": None if temporary else str(Path(path).expanduser().resolve()), "lines": lines,
            })
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="OCR_ERROR")
        finally:
            if temporary:
                Path(temporary["path"]).unlink(missing_ok=True)
