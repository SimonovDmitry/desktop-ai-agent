import time

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


def _get_keyboard(context):
    if hasattr(context.services, "system") and hasattr(context.services.system, "keyboard"):
        return context.services.system.keyboard
    if hasattr(context.services, "input") and hasattr(context.services.input, "keyboard"):
        return context.services.input.keyboard
    return getattr(context.services, "keyboard", None)


def _get_clipboard(context):
    if hasattr(context.services, "system") and hasattr(context.services.system, "clipboard"):
        return context.services.system.clipboard
    if hasattr(context.services, "input") and hasattr(context.services.input, "clipboard"):
        return context.services.input.clipboard
    return getattr(context.services, "clipboard", None)


class CopyText(Action):
    name = "copy_text"
    description = "Triggers 'Copy' command in the UI and retrieves the copied text"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            _get_keyboard(context).copy()
            time.sleep(0.05)
            text = _get_clipboard(context).get_clipboard()
            return ActionResult(success=True, data={"copied": True, "text": text or ""})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class PasteText(Action):
    discoverable = False
    name = "paste_text"
    description = "Place specific text into the clipboard and trigger the 'Paste' command"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {"text": {"type": "string", "required": True, "description": "Text to paste"}}

    def execute(self, context, parameters):
        p = parameters or {}
        text = p.get("text")
        if text is None:
            return ActionResult(success=False, error="Parameter 'text' is required", error_code="MISSING_PARAM")

        try:
            _get_clipboard(context).set_clipboard(text)
            _get_keyboard(context).paste()
            return ActionResult(success=True, data={"pasted": True, "text_length": len(text)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetSelectedText(Action):
    name = "get_selected_text"
    description = "Try to retrieve currently selected text from the active UI element"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            cb = _get_clipboard(context)
            cb.get_clipboard()
            _get_keyboard(context).copy()
            time.sleep(0.05)
            selected_text = cb.get_clipboard()
            return ActionResult(success=True, data={"selected": True, "text": selected_text or ""})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ReplaceSelectedText(Action):
    name = "replace_selected_text"
    description = "Replace the current selection with new text"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {"text": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        p = parameters or {}
        text = p.get("text")
        if text is None:
            return ActionResult(success=False, error="Missing text", error_code="MISSING_PARAM")

        try:
            _get_clipboard(context).set_clipboard(text)
            _get_keyboard(context).paste()
            return ActionResult(success=True, data={"replaced": True, "text_length": len(text)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class AppendToClipboard(Action):
    name = "append_to_clipboard"
    description = "Add text to the end of the current clipboard content"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "text": {"type": "string", "required": True},
        "separator": {"type": "string", "required": False, "default": "\n"},
    }

    def execute(self, context, parameters):
        p = parameters or {}
        text = p.get("text", "")
        separator = p.get("separator", "\n")

        try:
            cb = _get_clipboard(context)
            current = cb.get_clipboard()
            if current:
                expected = f"{current}{separator}{text}"
            else:
                expected = text
            cb.set_clipboard(expected)
            return ActionResult(success=True, data={"appended": True, "text_length": len(expected)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ClearClipboard(Action):
    name = "clear_clipboard"
    description = "Completely clear the system clipboard"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            cb = _get_clipboard(context)
            if hasattr(cb, "clean_clipboard"):
                cb.clean_clipboard()
            elif hasattr(cb, "clear_clipboard"):
                cb.clear_clipboard()
            elif hasattr(cb, "clear"):
                cb.clear()
            return ActionResult(success=True, data={"cleared": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))
