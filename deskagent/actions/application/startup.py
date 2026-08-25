from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetLoginItems(Action):
    name = "get_login_items"
    description = "Get a list of all applications configured to launch at user login"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            items = context.services.application.startup.get_all()
            return ActionResult(success=True, data={"applications": items})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class IsApplicationStartupEnabled(Action):
    name = "is_application_startup_enabled"
    description = "Check if a specific application is in the system startup/login items list"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            is_enabled = context.services.application.startup.is_enabled(app_name)
            return ActionResult(success=True, data={"enabled": is_enabled, "application": app_name})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class AddApplicationToStartup(Action):
    name = "add_application_to_startup"
    description = "Add an application to the system login items list"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    reversible = True
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        if not app_name: return ActionResult(success=False, error="Missing app name")

        try:
            context.services.application.startup.add(app_name)
            return ActionResult(success=True, data={"application": app_name, "added": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RemoveApplicationFromStartup(Action):
    name = "remove_application_from_startup"
    description = "Remove an application from the system login items list"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    reversible = True
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            context.services.application.startup.remove(app_name)
            return ActionResult(success=True, data={"application": app_name, "removed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class EnableApplicationStartup(Action):
    name = "enable_application_startup"
    description = "Enable an existing startup item"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            context.services.application.startup.enable(app_name)
            return ActionResult(success=True, data={"application": app_name, "enabled": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class DisableApplicationStartup(Action):
    name = "disable_application_startup"
    description = "Disable an existing startup item without removing it"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            context.services.application.startup.disable(app_name)
            return ActionResult(success=True, data={"application": app_name, "enabled": False})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))