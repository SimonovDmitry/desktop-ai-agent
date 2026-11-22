"""Actions for observable macOS accessibility dialogs and sheets."""

from __future__ import annotations

from pathlib import Path
import time

from deskagent.actions.accessibility.common import AccessibilityAction
from deskagent.actions.accessibility.safety import redact_secure_values
from deskagent.actions.types import ActionResult, RiskLevel
from deskagent.perception.accessibility import serialize_element
from deskagent.perception.accessibility.locator import normalize_text
from deskagent.perception.accessibility.tree import flatten_tree


DIALOG_SCHEMA = {"application": {"type": "string", "required": False}}


def _dialog(client, application=None):
    root = client.window_tree(application, max_depth=10, max_nodes=1500)
    candidates = [item for item in flatten_tree(root) if item.role in {"AXDialog", "AXSheet"} or item.subrole in {
        "AXDialog", "AXSystemDialog", "AXSheet"
    }]
    if not candidates:
        raise LookupError("No accessible dialog or sheet is active")
    return candidates[0]


def _dialog_elements(dialog):
    return flatten_tree(dialog)


def _button(dialog, label):
    buttons = [item for item in _dialog_elements(dialog) if item.role == "AXButton" and item.enabled]
    matches = [item for item in buttons if normalize_text(item.title or item.description) == normalize_text(label)]
    if len(matches) != 1:
        raise LookupError(f"Expected one enabled dialog button named {label!r}; found {len(matches)}")
    return matches[0]


class GetActiveDialog(AccessibilityAction):
    name = "get_active_dialog"
    description = "Read the active accessible dialog or sheet and its controls"
    parameters_schema = DIALOG_SCHEMA

    def execute(self, context, parameters):
        try:
            dialog = _dialog(self.client(context), (parameters or {}).get("application"))
            return ActionResult(True, {"dialog": redact_secure_values(serialize_element(dialog))})
        except Exception as exc:
            return self.failure(exc)


class SetDialogField(AccessibilityAction):
    name = "set_dialog_field"
    description = "Set a dialog text field by its AX locator and verify the value read back"
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        **DIALOG_SCHEMA,
        "element": {"type": "string", "required": True},
        "value": {"type": "string", "required": True},
    }

    def execute(self, context, parameters):
        try:
            client = self.client(context)
            dialog = _dialog(client, parameters.get("application"))
            fields = [
                item for item in _dialog_elements(dialog)
                if item.id == parameters["element"] or item.locator == parameters["element"]
            ]
            if len(fields) != 1 or fields[0].role not in {"AXTextField", "AXTextArea", "AXSearchField", "AXComboBox"}:
                raise ValueError("Element is not a text field in the active dialog")
            field = fields[0]
            if field.subrole == "AXSecureTextField":
                raise ValueError("Secure dialog fields require a separate secret input action")
            result = client.set_value(field.id, parameters["value"])
            verified = str(result.value) == parameters["value"]
            return ActionResult(verified, {"element": field.locator, "verified": verified},
                                None if verified else "Dialog field value did not match",
                                None if verified else "VERIFICATION_FAILED")
        except Exception as exc:
            return self.failure(exc)


class ConfirmDialog(AccessibilityAction):
    name = "confirm_dialog"
    description = "Press a specifically named dialog button and verify that the dialog closes"
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    parameters_schema = {**DIALOG_SCHEMA, "button": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        try:
            client = self.client(context)
            dialog = _dialog(client, parameters.get("application"))
            button = _button(dialog, parameters["button"])
            client._backend().perform_action(client._reference(button), "AXPress")
            try:
                after = _dialog(client, parameters.get("application"))
            except LookupError:
                return ActionResult(True, {"button": parameters["button"], "closed": True})
            if after.locator != dialog.locator:
                return ActionResult(True, {"button": parameters["button"], "closed": True})
            return ActionResult(False, {"button": parameters["button"], "closed": False},
                                "Dialog is still open", "VERIFICATION_FAILED")
        except Exception as exc:
            return self.failure(exc)


class CancelDialog(AccessibilityAction):
    name = "cancel_dialog"
    description = "Press the exact Cancel button in the active dialog"
    parameters_schema = {**DIALOG_SCHEMA, "button": {"type": "string", "required": False, "default": "Cancel"}}

    def execute(self, context, parameters):
        try:
            client = self.client(context)
            dialog = _dialog(client, parameters.get("application"))
            label = parameters.get("button", "Cancel")
            button = _button(dialog, label)
            client._backend().perform_action(client._reference(button), "AXPress")
            try:
                _dialog(client, parameters.get("application"))
            except LookupError:
                return ActionResult(True, {"closed": True})
            return ActionResult(False, {"closed": False}, "Dialog is still open", "VERIFICATION_FAILED")
        except Exception as exc:
            return self.failure(exc)


class ReadPermissionPrompt(AccessibilityAction):
    name = "read_permission_prompt"
    description = "Read text and available buttons in the active system permission dialog"
    parameters_schema = DIALOG_SCHEMA

    def execute(self, context, parameters):
        try:
            dialog = _dialog(self.client(context), (parameters or {}).get("application"))
            elements = _dialog_elements(dialog)
            return ActionResult(True, {
                "application": dialog.application, "title": dialog.title,
                "text": [
                    str(item.value or item.title) for item in elements
                    if item.role == "AXStaticText" and (item.value or item.title)
                ],
                "buttons": [item.title for item in elements if item.role == "AXButton" and item.title],
            })
        except Exception as exc:
            return self.failure(exc)


class ChooseFileInDialog(AccessibilityAction):
    name = "choose_file_in_dialog"
    description = "Navigate a standard file dialog to a folder and select a file by exact name"
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {**DIALOG_SCHEMA, "path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        try:
            path = Path(parameters["path"]).expanduser().resolve()
            if not path.is_file():
                raise FileNotFoundError(path)
            client = self.client(context)
            _dialog(client, parameters.get("application"))
            context.services.input.shortcuts.press_shortcut("cmd+shift+g")
            deadline = time.monotonic() + 5
            folder_field = None
            while time.monotonic() < deadline:
                dialog = _dialog(client, parameters.get("application"))
                fields = [item for item in _dialog_elements(dialog) if item.role in {"AXTextField", "AXComboBox"}]
                folder_field = next((item for item in fields if item.focused), None)
                if folder_field:
                    break
                time.sleep(0.1)
            if folder_field is None:
                raise LookupError("Go to Folder input was not found")
            value = client.set_value(folder_field.id, str(path.parent))
            if str(value.value) != str(path.parent):
                raise RuntimeError("Go to Folder path could not be verified")
            context.services.input.keyboard.tap_key("enter")
            candidates = []
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                dialog = _dialog(client, parameters.get("application"))
                candidates = [
                    item for item in _dialog_elements(dialog)
                    if normalize_text(item.title or item.value) == normalize_text(path.name)
                ]
                if candidates:
                    break
                time.sleep(0.1)
            if len(candidates) != 1:
                raise LookupError("File was not uniquely visible in the dialog after navigation")
            selected = client.set_selected(candidates[0].id, True)
            if not selected.selected:
                return ActionResult(False, {"path": str(path), "selected": False},
                                    "File selection could not be verified", "VERIFICATION_FAILED")
            return ActionResult(True, {"path": str(path), "selected": True})
        except Exception as exc:
            return self.failure(exc)
