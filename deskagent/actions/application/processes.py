from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


class GetApplicationProcesses(Action):
    name = "get_application_processes"
    description = "Get all system processes associated with a specific application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {"application": {"type": "string", "required": True, "description": "Name of the application"}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            processes = context.services.application.processes.get_processes(app_name)
            return ActionResult(success=True, data={"processes": processes})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetApplicationProcessTree(Action):
    name = "get_application_process_tree"
    description = "Get the hierarchical tree of processes for an application"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            srv = context.services.application.processes
            tree = srv.get_process_tree(app_name) if hasattr(srv, "get_process_tree") else srv.get_tree(app_name)
            return ActionResult(success=True, data=tree)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetApplicationMainProcess(Action):
    name = "get_application_main_process"
    description = "Identify the primary (parent) process of an application"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            srv = context.services.application.processes
            main_proc = srv.get_main_process(app_name) if hasattr(srv, "get_main_process") else srv.get_main(app_name)
            return ActionResult(success=True, data=main_proc)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetApplicationChildProcesses(Action):
    name = "get_application_child_processes"
    description = "Get all secondary (child) processes spawned by an application"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            srv = context.services.application.processes
            children = (
                srv.get_child_processes(app_name) if hasattr(srv, "get_child_processes") else srv.get_children(app_name)
            )
            return ActionResult(success=True, data={"processes": children})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SuspendApplication(Action):
    name = "suspend_application"
    description = "Pause the execution of an application (Freeze it)"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    reversible = True
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            context.services.application.processes.suspend(app_name)
            return ActionResult(success=True, data={"application": app_name, "suspended": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ResumeApplication(Action):
    name = "resume_application"
    description = "Resume the execution of a previously suspended application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            context.services.application.processes.resume(app_name)
            return ActionResult(success=True, data={"application": app_name, "resumed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
