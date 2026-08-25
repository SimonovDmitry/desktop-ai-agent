from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetApplicationInstances(Action):
    name = "get_application_instances"
    description = "Get all running instances of a specific application with their PIDs"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "application": {
            "type": "string",
            "required": True,
            "description": "Name of the application"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            instances = context.services.application.instances.get_all(app_name)
            return ActionResult(success=True, data={"instances": instances})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetApplicationInstanceCount(Action):
    name = "get_application_instance_count"
    description = "Get the number of running instances for a specific application"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            count = context.services.application.instances.get_count(app_name)
            return ActionResult(success=True, data={"count": count, "application": app_name})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ActivateApplicationInstance(Action):
    name = "activate_application_instance"
    description = "Bring a specific instance of an application to focus using its PID"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "application": {"type": "string", "required": False, "description": "Optional name for context"},
        "pid": {"type": "integer", "required": True, "description": "The specific Process ID to activate"}
    }

    def execute(self, context, parameters):
        params = parameters or {}
        pid = params.get('pid')
        if pid is None:
            return ActionResult(success=False, error="Parameter 'pid' is required", error_code="MISSING_PARAM")

        try:
            context.services.application.instances.activate(pid)
            return ActionResult(success=True, data={"pid": pid, "active": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="NOT_FOUND")


class QuitApplicationInstance(Action):
    name = "quit_application_instance"
    description = "Gracefully quit a specific instance of an application by its PID"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "application": {"type": "string", "required": False},
        "pid": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        params = parameters or {}
        pid = params.get('pid')
        if pid is None:
            return ActionResult(success=False, error="Parameter 'pid' is required", error_code="MISSING_PARAM")

        try:
            context.services.application.instances.quit(pid)
            return ActionResult(success=True, data={"pid": pid, "quit": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
