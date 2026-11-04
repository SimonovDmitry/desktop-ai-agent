from __future__ import annotations

import platform

from deskagent.perception.accessibility.models import UnsupportedAccessibilityError

SETTINGS_URL = (
    "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
)


def get_accessibility_status() -> dict:
    if platform.system() != "Darwin":
        return {
            "supported": False,
            "trusted": False,
            "status": "unavailable",
            "instruction": "Accessibility is currently supported only on macOS.",
        }
    try:
        from ApplicationServices import AXIsProcessTrusted

        trusted = bool(AXIsProcessTrusted())
        return {
            "supported": True,
            "trusted": trusted,
            "status": "granted" if trusted else "denied",
            "instruction": "Enable this app in System Settings → Privacy & Security → Accessibility.",
        }
    except ImportError as exc:
        raise UnsupportedAccessibilityError(
            "PyObjC ApplicationServices is not installed"
        ) from exc


def request_accessibility_permission(prompt: bool = True) -> dict:
    if platform.system() != "Darwin":
        return get_accessibility_status()
    try:
        from ApplicationServices import (
            AXIsProcessTrustedWithOptions,
            kAXTrustedCheckOptionPrompt,
        )

        trusted = bool(
            AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: bool(prompt)})
        )
        result = get_accessibility_status()
        result["trusted"] = trusted
        result["status"] = "granted" if trusted else "denied"
        result["prompt_requested"] = bool(prompt)
        return result
    except ImportError as exc:
        raise UnsupportedAccessibilityError(
            "PyObjC ApplicationServices is not installed"
        ) from exc
