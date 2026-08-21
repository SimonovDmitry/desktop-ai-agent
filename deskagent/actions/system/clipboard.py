from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.context import ActionContext
from deskagent.actions.types import RiskLevel, ActionCategory


class GetClipboard(Action):
    name = "get_clipboard"
    description = "Get the current text content from the system clipboard"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
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

    def execute(self, context, text):
        if text is None:
            return ActionResult(success=False, error="Text content must be provided", error_code="INVALID_INPUT")

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

    def execute(self, context):
        try:
            context.services.system.clipboard.clean_clipboard()
            return ActionResult(success=True, data={"cleared": True})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")