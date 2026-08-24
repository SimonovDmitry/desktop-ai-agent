from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class SendNotification(Action):
    name = "send_notification"
    description = "Send a system notification to the user"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "title": {
            "type": "string",
            "required": True,
            "description": "Bold title of the notification"
        },
        "message": {
            "type": "string",
            "required": True,
            "description": "Main body text of the notification"
        },
        "subtitle": {
            "type": "string",
            "required": False,
            "description": "Secondary title (optional)"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        title = params.get('title')
        message = params.get('message')
        subtitle = params.get('subtitle')

        if not title or not message:
            return ActionResult(
                success=False,
                error="Parameters 'title' and 'message' are required",
                error_code="MISSING_PARAM"
            )

        try:
            # Вызываем метод из платформенного сервиса уведомлений
            context.services.system.notify.send_notification(title, message, subtitle)
            return ActionResult(success=True, data={"title": title, "message": message, "subtitle": subtitle})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать логику очистки уведомлений в платформенном сервисе (если ОС это позволяет)
class ClearAgentNotification(Action):
    name = "clear_agent_notification"
    description = "Clear all notifications sent by the DeskAgent"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            result = context.services.system.notify.clear_agent_notification()
            return ActionResult(success=True, data={"status": result})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")