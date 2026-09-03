from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory
import time


class CopyText(Action):
    name = "copy_text"
    description = "Triggers 'Copy' command in the UI and retrieves the copied text"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.keyboard.copy()
            time.sleep(0.1)
            text = context.services.system.clipboard.get_clipboard()

            return ActionResult(success=True, data={
                "copied": True,
                "text": text or ""
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class PasteText(Action):
    name = "paste_text"
    description = "Place specific text into the clipboard and trigger the 'Paste' command"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "text": {"type": "string", "required": True, "description": "Text to paste"}
    }

    def execute(self, context, parameters):
        text = parameters.get('text')
        if text is None:
            return ActionResult(success=False, error="Parameter 'text' is required", error_code="MISSING_PARAM")

        try:
            context.services.system.clipboard.set_clipboard(text)
            context.services.system.keyboard.paste()

            return ActionResult(success=True, data={
                "pasted": True,
                "text_length": len(text)
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetSelectedText(Action):
    name = "get_selected_text"
    description = "Try to retrieve currently selected text from the active UI element"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            old_content = context.services.system.clipboard.get_clipboard()

            context.services.system.keyboard.copy()
            time.sleep(0.1)
            selected_text = context.services.system.clipboard.get_clipboard()
            return ActionResult(success=True, data={
                "selected": True,
                "text": selected_text or ""
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ReplaceSelectedText(Action):
    name = "replace_selected_text"
    description = "Replace the current selection with new text"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "text": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        text = parameters.get('text')
        if text is None: return ActionResult(success=False, error="Missing text")

        try:
            context.services.system.clipboard.set_clipboard(text)
            context.services.system.keyboard.paste()

            return ActionResult(success=True, data={
                "replaced": True,
                "text_length": len(text)
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class AppendToClipboard(Action):
    name = "append_to_clipboard"
    description = "Add text to the end of the current clipboard content"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "text": {"type": "string", "required": True},
        "separator": {"type": "string", "required": False, "default": "\n"}
    }

    def execute(self, context, parameters):
        text = parameters.get('text')
        separator = parameters.get('separator', "\n")

        try:
            current = context.services.system.clipboard.get_clipboard() or ""
            new_content = current + separator + text if current else text

            context.services.system.clipboard.set_clipboard(new_content)
            return ActionResult(success=True, data={
                "appended": True,
                "text_length": len(new_content)
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ClearClipboard(Action):
    name = "clear_clipboard"
    description = "Completely clear the system clipboard"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.clipboard.clean_clipboard()
            return ActionResult(success=True, data={"cleared": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))