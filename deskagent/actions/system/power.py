from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class LockScreen(Action):
    name = "lock_screen"
    description = "Lock the computer screen immediately"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.power.lock_screen()
            return ActionResult(success=True, data={"status": "locked"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SleepComputer(Action):
    name = "sleep_computer"
    description = "Put the computer into sleep mode"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.power.sleep_computer()
            return ActionResult(success=True, data={"status": "sleeping"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class RestartComputer(Action):
    name = "restart_computer"
    description = "Restart the computer"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.power.restart_computer()
            return ActionResult(success=True, data={"status": "restarting"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ShutdownComputer(Action):
    name = "shutdown_computer"
    description = "Shut down the computer"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.power.shutdown_computer()
            return ActionResult(success=True, data={"status": "shutting_down"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать метод выхода из системы в платформенном сервисе
class LogoutComputer(Action):
    name = "logout_computer"
    description = "Log out the current user"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.power.logout_computer()
            return ActionResult(success=True, data={"status": "logging_out"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать метод отмены выключения (если поддерживается ОС)
class CancelShutdownComputer(Action):
    name = "cancel_shutdown_computer"
    description = "Cancel a scheduled system shutdown or restart"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.power.cancel_shutdown_computer()
            return ActionResult(success=True, data={"status": "cancelled"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")