"""Read-only diagnostics for the currently configured agent runtime."""

from __future__ import annotations

import platform
from importlib.util import find_spec
from pathlib import Path

from deskagent.actions.base import Action
from deskagent.actions.registry import discover_actions
from deskagent.actions.types import ActionCategory, ActionResult
from deskagent.core.permissions import PermissionManager


UNSUPPORTED_BROWSER_ACTIONS = {
    "pin_browser_tab", "unpin_browser_tab", "move_browser_tab", "reopen_closed_tab", "delete_browser_history"
}
MACOS_ACTION_MODULES = (
    "deskagent.actions.music.", "deskagent.actions.vision.",
    "deskagent.actions.audio.system", "deskagent.actions.audio.convert",
)


def _action_classes():
    return {action.name: action for action in discover_actions(include_plugins=False)}


def _availability(context, name):
    action = _action_classes().get(name)
    if action is None:
        return {"action": name, "available": False, "reason": "Action is not registered"}
    if name in UNSUPPORTED_BROWSER_ACTIONS:
        return {"action": name, "available": False, "reason": "No current browser backend implements this action"}
    if platform.system() != "Darwin" and action.category in {
        ActionCategory.ACCESSIBILITY, ActionCategory.APPLICATION, ActionCategory.WINDOW,
        ActionCategory.INPUT, ActionCategory.NOTES,
    }:
        return {"action": name, "available": False, "reason": "The desktop backend requires macOS"}
    if action.category is ActionCategory.NOTES and not Path("/System/Applications/Notes.app").is_dir():
        return {"action": name, "available": False, "reason": "Apple Notes is not installed"}
    if action.__module__.startswith(MACOS_ACTION_MODULES):
        if platform.system() != "Darwin":
            return {"action": name, "available": False, "reason": "This action requires macOS"}
    if action.__module__.startswith("deskagent.actions.music."):
        if not Path("/System/Applications/Music.app").is_dir():
            return {"action": name, "available": False, "reason": "Apple Music is not installed"}
    if name == "read_screen_text" and find_spec("Vision") is None:
        return {"action": name, "available": False, "reason": "pyobjc-framework-Vision is not installed"}
    report = PermissionManager().check_action(action)
    if not report.granted:
        return {"action": name, "available": False, "reason": report.error, "permissions": report.to_dict()}
    return {"action": name, "available": True, "permissions": report.to_dict()}


class GetAgentCapabilities(Action):
    name = "get_agent_capabilities"
    description = "Report supported platform, configured vision and audio, and desktop permission states"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        manager = PermissionManager()
        report = manager.check(("accessibility", "screen_recording", "automation", "microphone", "notifications"))
        browsers, browser_error = [], None
        browser_service = getattr(context.services, "browser", None)
        if browser_service is not None:
            try:
                browser_service.configure(context.settings)
                browsers = [item.to_dict() for item in browser_service.list_browsers()]
            except Exception as exc:
                browser_error = str(exc)
        return ActionResult(True, {
            "platform": platform.system(),
            "vision_background_enabled": bool(context.settings.vision.enabled),
            "vision_ocr_installed": find_spec("Vision") is not None,
            "audio_enabled": bool(context.settings.audio.enabled),
            "permissions": report.to_dict(),
            "browsers": browsers,
            "browser_error": browser_error,
        })


class CheckActionAvailability(Action):
    name = "check_action_availability"
    description = "Check whether a registered action can run with the current platform and permissions"
    category = ActionCategory.SYSTEM
    parameters_schema = {"action": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        try:
            return ActionResult(True, _availability(context, parameters["action"]))
        except Exception as exc:
            return ActionResult(False, error=str(exc), error_code="CAPABILITY_ERROR")
