from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.context import ActionContext
from deskagent.actions.types import RiskLevel, ActionCategory

# TODO
class SendNotification(Action):
    name = "send_notification"
    description = "Send a system notification to the user"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context, title, message, subtitle=None):
        if not message:
            return ActionResult(success=False, error="Notification message cannot be empty", error_code="INVALID_INPUT")

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

    def execute(self, context):
        try:
            result = context.services.system.notify.clear_agent_notification()
            return ActionResult(success=True, data={"status": result})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
