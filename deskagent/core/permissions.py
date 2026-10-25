import platform
import threading
from dataclasses import dataclass
from enum import Enum


class Permission(str, Enum):
    ACCESSIBILITY = "accessibility"
    SCREEN_RECORDING = "screen_recording"
    AUTOMATION = "automation"
    MICROPHONE = "microphone"
    NOTIFICATIONS = "notifications"


class PermissionState(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    NOT_DETERMINED = "not_determined"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PermissionStatus:
    permission: Permission
    state: PermissionState
    instruction: str = ""

    @property
    def granted(self):
        return self.state == PermissionState.GRANTED

    def to_dict(self):
        return {"permission": self.permission.value, "state": self.state.value,
                "instruction": self.instruction}


@dataclass(frozen=True)
class PermissionReport:
    statuses: tuple[PermissionStatus, ...]

    @property
    def granted(self):
        return all(status.granted for status in self.statuses)

    @property
    def error(self):
        denied = [status for status in self.statuses if not status.granted]
        return "; ".join(f"{item.permission.value}: {item.state.value}. {item.instruction}" for item in denied)

    def to_dict(self):
        return {"granted": self.granted, "statuses": [status.to_dict() for status in self.statuses]}


class PermissionManager:
    INSTRUCTIONS = {
        Permission.ACCESSIBILITY: "Enable the app in System Settings → Privacy & Security → Accessibility.",
        Permission.SCREEN_RECORDING: "Enable the app in System Settings → Privacy & Security → Screen & System Audio Recording.",
        Permission.AUTOMATION: "Allow the app to control the target app in System Settings → Privacy & Security → Automation.",
        Permission.MICROPHONE: "Enable the app in System Settings → Privacy & Security → Microphone.",
        Permission.NOTIFICATIONS: "Enable notifications for the app in System Settings → Notifications.",
    }

    def __init__(self, system=None):
        self.system = (system or platform.system()).lower()

    def status(self, permission: Permission | str):
        permission = Permission(permission)
        if self.system != "darwin":
            return PermissionStatus(permission, PermissionState.UNAVAILABLE, "Permission checks are implemented for macOS.")
        checker = getattr(self, f"_{permission.value}")
        try:
            return PermissionStatus(permission, checker(), self.INSTRUCTIONS[permission])
        except Exception as exc:
            return PermissionStatus(permission, PermissionState.UNAVAILABLE,
                                    f"{self.INSTRUCTIONS[permission]} Checker error: {exc}")

    def check(self, permissions):
        return PermissionReport(tuple(self.status(permission) for permission in permissions))

    def check_action(self, action):
        permissions = set(action.required_permissions)
        module = action.__module__
        if (".actions.input." in module or ".actions.window." in module
                or module.endswith("actions.system.mouse")):
            permissions.add(Permission.ACCESSIBILITY.value)
        if module.endswith("actions.system.notification"):
            permissions.add(Permission.NOTIFICATIONS.value)
        return self.check(sorted(permissions))

    @staticmethod
    def _accessibility():
        from ApplicationServices import AXIsProcessTrusted
        return PermissionState.GRANTED if AXIsProcessTrusted() else PermissionState.DENIED

    @staticmethod
    def _screen_recording():
        from Quartz import CGPreflightScreenCaptureAccess
        return PermissionState.GRANTED if CGPreflightScreenCaptureAccess() else PermissionState.DENIED

    @staticmethod
    def _automation():
        return PermissionState.UNKNOWN

    @staticmethod
    def _microphone():
        from AVFoundation import AVCaptureDevice, AVMediaTypeAudio
        status = int(AVCaptureDevice.authorizationStatusForMediaType_(AVMediaTypeAudio))
        return {0: PermissionState.NOT_DETERMINED, 2: PermissionState.DENIED,
                3: PermissionState.GRANTED}.get(status, PermissionState.UNKNOWN)

    @staticmethod
    def _notifications():
        from UserNotifications import UNUserNotificationCenter
        done, result = threading.Event(), {}

        def callback(settings):
            try:
                result["status"] = int(settings.authorizationStatus()) if settings else -1
            except Exception:
                result["status"] = -1
            finally:
                done.set()

        UNUserNotificationCenter.currentNotificationCenter().getNotificationSettingsWithCompletionHandler_(callback)
        if not done.wait(2):
            return PermissionState.UNKNOWN
        return {0: PermissionState.NOT_DETERMINED, 1: PermissionState.DENIED,
                2: PermissionState.GRANTED, 3: PermissionState.GRANTED,
                4: PermissionState.GRANTED}.get(result["status"], PermissionState.UNKNOWN)
