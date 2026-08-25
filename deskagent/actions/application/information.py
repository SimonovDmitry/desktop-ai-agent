from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetRunningApplications(Action):
    name = "get_running_applications"
    description = "Get a list of all currently running applications with their PIDs"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            apps = context.services.application.information.get_running()
            return ActionResult(success=True, data={"applications": apps})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetInstalledApplications(Action):
    name = "get_installed_applications"
    description = "Get a list of all applications installed on the system"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            apps = context.services.application.information.get_installed()
            return ActionResult(success=True, data={"applications": apps})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class FindApplications(Action):
    name = "find_applications"
    description = "Search for applications by name or keyword"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "query": {"type": "string", "required": True, "description": "Search term"},
        "limit": {"type": "integer", "required": False, "default": 10}
    }

    def execute(self, context, parameters):
        params = parameters or {}
        query = params.get('query')
        limit = params.get('limit', 10)

        if not query:
            return ActionResult(success=False, error="Query parameter is required", error_code="MISSING_PARAM")

        try:
            apps = context.services.application.information.find(query, limit)
            return ActionResult(success=True, data={"applications": apps})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetApplicationInfo(Action):
    name = "get_application_info"
    description = "Get full technical details about a specific application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        if not app_name: return ActionResult(success=False, error="Missing app name")

        try:
            info = context.services.application.information.get_info(app_name)
            return ActionResult(success=True, data=info)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="NOT_FOUND")


class GetApplicationStatus(Action):
    name = "get_application_status"
    description = "Get the operational state of an app (running, visible, active)"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            status = context.services.application.information.get_status(app_name)
            return ActionResult(success=True, data=status)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsApplicationRunning(Action):
    name = "is_application_running"
    description = "Simple check if an application is running"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            running = context.services.application.information.is_running(app_name)
            return ActionResult(success=True, data={"running": running})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetActiveApplication(Action):
    name = "get_active_application"
    description = "Get information about the application currently in focus"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            active = context.services.application.information.get_active()
            return ActionResult(success=True, data=active)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetApplicationPID(Action):
    name = "get_application_pid"
    description = "Get the Process ID of an application"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            pid = context.services.application.information.get_pid(app_name)
            return ActionResult(success=True, data={"pid": pid})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetApplicationPath(Action):
    name = "get_application_path"
    description = "Get the file system path of an application (.app bundle)"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            path = context.services.application.information.get_path(app_name)
            return ActionResult(success=True, data={"path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetApplicationExecutablePath(Action):
    name = "get_application_executable_path"
    description = "Get the path to the actual binary executable of an application"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            executable = context.services.application.information.get_executable_path(app_name)
            return ActionResult(success=True, data={"executable": executable})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetApplicationBundleId(Action):
    name = "get_application_bundle_id"
    description = "Get the unique system identifier (Bundle ID) of an app"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            bundle_id = context.services.application.information.get_bundle_id(app_name)
            return ActionResult(success=True, data={"bundle_id": bundle_id})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetApplicationVersion(Action):
    name = "get_application_version"
    description = "Get the version string of an application"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            version = context.services.application.information.get_version(app_name)
            return ActionResult(success=True, data={"version": version})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetApplicationArchitecture(Action):
    name = "get_application_architecture"
    description = "Get the CPU architecture of the app (arm64, x86_64)"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            arch = context.services.application.information.get_architecture(app_name)
            return ActionResult(success=True, data={"architecture": arch})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetApplicationName(Action):
    name = "get_application_name"
    description = "Identify the application name from a PID, path, or bundle ID"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "identifier_type": {
            "type": "string",
            "required": True,
            "enum": ["pid", "path", "bundle_id"]
        },
        "identifier": {
            "type": "string_or_int",
            "required": True
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        id_type = params.get('identifier_type')
        val = params.get('identifier')

        if not id_type or val is None:
            return ActionResult(success=False, error="Both identifier_type and identifier are required",
                                error_code="MISSING_PARAM")

        try:
            name = context.services.application.information.get_name_from_id(id_type, val)
            return ActionResult(success=True, data={"name": name})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="NOT_FOUND")