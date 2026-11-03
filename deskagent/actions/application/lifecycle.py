from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


class LaunchApplication(Action):
    name = "launch_application"
    description = "Launch an application by its name"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "application": {"type": "string", "required": True, "description": "Name of the application to launch"}
    }

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            result = context.services.application.lifecycle.launch(app_name)
            pid = result.get("pid") if isinstance(result, dict) else result
            return ActionResult(
                success=True, data={"application": app_name, "pid": pid, "launched": True}
            )
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class LaunchApplicationWithArguments(Action):
    name = "launch_application_with_arguments"
    description = "Launch an application with specific command-line arguments"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "application": {"type": "string", "required": True},
        "arguments": {"type": "list", "required": True, "description": "List of strings (e.g. ['--incognito'])"},
    }

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        args = params.get("arguments")
        if not app_name or args is None:
            return ActionResult(
                success=False, error="Application and arguments are required", error_code="MISSING_PARAM"
            )

        try:
            result = context.services.application.lifecycle.launch(app_name, arguments=args)
            pid = result.get("pid") if isinstance(result, dict) else result
            return ActionResult(
                success=True, data={"application": app_name, "pid": pid, "launched": True}
            )
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class LaunchApplicationHidden(Action):
    name = "launch_application_hidden"
    description = "Launch an application without bringing its window to focus"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            result = context.services.application.lifecycle.launch_hidden(app_name)
            pid = result.get("pid") if isinstance(result, dict) else result
            return ActionResult(
                success=True,
                data={"application": app_name, "pid": pid, "launched": True, "hidden": True},
            )
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class QuitApplication(Action):
    name = "quit_application"
    description = "Gracefully quit an application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            context.services.application.lifecycle.quit(app_name)
            return ActionResult(success=True, data={"application": app_name, "quit": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ForceQuitApplication(Action):
    name = "force_quit_application"
    description = "Forcefully terminate an application. WARNING: Potential data loss."
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    reversible = False
    parameters_schema = {"application": {"type": "string_or_int", "required": True, "description": "App name or PID"}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_id = params.get("application")
        if app_id is None:
            return ActionResult(
                success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM"
            )

        try:
            context.services.application.lifecycle.force_quit(app_id)
            return ActionResult(success=True, data={"application": app_id, "terminated": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class RestartApplication(Action):
    name = "restart_application"
    description = "Restart an application (Quit and Launch again)"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    reversible = False
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            context.services.application.lifecycle.restart(app_name)
            return ActionResult(success=True, data={"application": app_name, "restarted": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class WaitForApplication(Action):
    name = "wait_for_application"
    description = "Wait until an application starts running"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "application": {"type": "string", "required": True},
        "timeout": {"type": "integer", "required": False, "default": 30},
    }

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        timeout = params.get("timeout")
        if timeout is None:
            return ActionResult(success=False, error="Parameter 'timeout' is required", error_code="MISSING_PARAM")
        if not isinstance(timeout, int) or timeout <= 0:
            return ActionResult(success=False, error="Timeout must be a positive integer", error_code="INVALID_INPUT")

        try:
            result = context.services.application.lifecycle.wait_for_start(app_name, timeout)
            res_dict = result if isinstance(result, dict) else {}
            return ActionResult(
                success=True,
                data={
                    "application": app_name,
                    "started": res_dict.get("started", True),
                    "pid": res_dict.get("pid"),
                    "waited": res_dict.get("waited"),
                },
            )
        except TimeoutError as exc:
            return ActionResult(success=False, error=str(exc), error_code="TIMEOUT")
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class WaitForApplicationExit(Action):
    name = "wait_for_application_exit"
    description = "Wait until an application is closed"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "application": {"type": "string", "required": True},
        "timeout": {"type": "integer", "required": False, "default": 30},
    }

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        timeout = params.get("timeout")
        if timeout is None:
            return ActionResult(success=False, error="Parameter 'timeout' is required", error_code="MISSING_PARAM")
        if not isinstance(timeout, int) or timeout <= 0:
            return ActionResult(success=False, error="Timeout must be a positive integer", error_code="INVALID_INPUT")

        try:
            result = context.services.application.lifecycle.wait_for_exit(app_name, timeout)
            res_dict = result if isinstance(result, dict) else {}
            return ActionResult(
                success=True,
                data={"application": app_name, "exited": True, "waited": res_dict.get("waited")},
            )
        except TimeoutError as exc:
            return ActionResult(success=False, error=str(exc), error_code="TIMEOUT")
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class LaunchOrActivateApplication(Action):
    name = "launch_or_activate_application"
    description = "Bring app to front if running, otherwise launch it"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            result = context.services.application.lifecycle.launch_or_activate(app_name)
            res_dict = result if isinstance(result, dict) else {}
            return ActionResult(
                success=True,
                data={
                    "application": app_name,
                    "action": res_dict.get("action"),
                    "pid": res_dict.get("pid") if isinstance(result, dict) else result,
                },
            )
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
