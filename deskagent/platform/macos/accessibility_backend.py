from __future__ import annotations

import platform
from typing import Any

from deskagent.platform.common.accessibility.locator import normalize_text
from deskagent.platform.common.accessibility.models import (
    AccessibilityError, ElementNotFoundError, Point, Size, UnsupportedAccessibilityError,
)


class MacOSAXBackend:
    """Thin, mockable wrapper around the PyObjC Accessibility functions."""

    def __init__(self):
        if platform.system() != "Darwin":
            raise UnsupportedAccessibilityError(
                "AXUIElement is available only on macOS"
            )
        try:
            import ApplicationServices as ax
            from AppKit import NSWorkspace
        except ImportError as exc:
            raise UnsupportedAccessibilityError(
                "PyObjC ApplicationServices and Cocoa are required"
            ) from exc
        self.ax = ax
        self.workspace = NSWorkspace.sharedWorkspace()

    def applications(self) -> list[dict[str, Any]]:
        result = []
        for app in self.workspace.runningApplications():
            name = app.localizedName()
            if name:
                result.append(
                    {
                        "name": str(name),
                        "pid": int(app.processIdentifier()),
                        "bundle_id": str(app.bundleIdentifier() or ""),
                    }
                )
        return result

    def application(self, name_or_pid: str | int | None = None):
        applications = self.applications()
        if name_or_pid is None:
            active = self.workspace.frontmostApplication()
            if active is None:
                raise ElementNotFoundError("No frontmost application")
            info = {
                "name": str(active.localizedName() or ""),
                "pid": int(active.processIdentifier()),
                "bundle_id": str(active.bundleIdentifier() or ""),
            }
        elif isinstance(name_or_pid, int) or str(name_or_pid).isdigit():
            pid = int(name_or_pid)
            info = next((item for item in applications if item["pid"] == pid), None)
        else:
            expected = normalize_text(name_or_pid)
            info = next(
                (
                    item
                    for item in applications
                    if normalize_text(item["name"]) == expected
                    or normalize_text(item["bundle_id"]) == expected
                ),
                None,
            )
            if info is None:
                info = next(
                    (
                        item
                        for item in applications
                        if expected in normalize_text(item["name"])
                    ),
                    None,
                )
        if not info:
            raise ElementNotFoundError(f"Running application not found: {name_or_pid}")
        return self.ax.AXUIElementCreateApplication(info["pid"]), info

    def system_wide(self):
        return self.ax.AXUIElementCreateSystemWide()

    def copy_attribute(self, ref, attribute: str, default=None):
        try:
            result = self.ax.AXUIElementCopyAttributeValue(ref, attribute, None)
        except Exception:
            return default
        if isinstance(result, tuple) and len(result) == 2:
            error, value = result
            return value if int(error) == 0 else default
        return result if result is not None else default

    def actions(self, ref) -> list[str]:
        try:
            result = self.ax.AXUIElementCopyActionNames(ref, None)
        except Exception:
            return []
        if isinstance(result, tuple) and len(result) == 2:
            error, result = result
            if int(error) != 0:
                return []
        return [str(value) for value in (result or [])]

    def set_attribute(self, ref, attribute: str, value) -> None:
        error = self.ax.AXUIElementSetAttributeValue(ref, attribute, value)
        if isinstance(error, tuple):
            error = error[0]
        if int(error or 0) != 0:
            raise AccessibilityError(f"Unable to set {attribute}: AX error {error}")

    def perform_action(self, ref, action: str) -> None:
        error = self.ax.AXUIElementPerformAction(ref, action)
        if isinstance(error, tuple):
            error = error[0]
        if int(error or 0) != 0:
            raise AccessibilityError(f"Unable to perform {action}: AX error {error}")

    def point(self, value) -> Point | None:
        result = self._ax_value(value, getattr(self.ax, "kAXValueCGPointType", 1))
        if result is None:
            return None
        try:
            return Point(float(result.x), float(result.y))
        except AttributeError:
            try:
                return Point(float(result[0]), float(result[1]))
            except (TypeError, IndexError, ValueError):
                return None

    def size(self, value) -> Size | None:
        result = self._ax_value(value, getattr(self.ax, "kAXValueCGSizeType", 2))
        if result is None:
            return None
        try:
            return Size(float(result.width), float(result.height))
        except AttributeError:
            try:
                return Size(float(result[0]), float(result[1]))
            except (TypeError, IndexError, ValueError):
                return None

    def _ax_value(self, value, value_type):
        if value is None:
            return None
        try:
            result = self.ax.AXValueGetValue(value, value_type, None)
        except Exception:
            return value
        if (
            isinstance(result, tuple)
            and len(result) == 2
            and isinstance(result[0], (bool, int))
        ):
            return result[1] if result[0] else None
        return result
