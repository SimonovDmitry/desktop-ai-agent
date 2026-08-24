from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetClipboard(Action):
    name = "get_clipboard"
    description = "Get the current text content from the system clipboard"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            content = context.services.system.clipboard.get_clipboard()
            if content is None:
                return ActionResult(success=True, data={"content": ""}, message="Clipboard is empty")

            return ActionResult(success=True, data={"content": content})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SetClipboard(Action):
    name = "set_clipboard"
    description = "Set new text content to the system clipboard"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "text": {
            "type": "string",
            "required": True,
            "description": "Text content to be placed on the clipboard"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        text = params.get('text')

        if text is None:
            return ActionResult(success=False, error="Parameter 'text' is required", error_code="MISSING_PARAM")

        try:
            context.services.system.clipboard.set_clipboard(text)
            return ActionResult(success=True, data={"text_length": len(text)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class CleanClipboard(Action):
    name = "clean_clipboard"
    description = "Clear all content from the system clipboard"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.clipboard.clean_clipboard()
            return ActionResult(success=True, data={"cleared": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")