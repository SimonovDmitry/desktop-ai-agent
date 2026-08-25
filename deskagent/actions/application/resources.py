from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetApplicationCPUUsage(Action):
    name = "get_application_cpu_usage"
    description = "Get the current CPU usage percentage for a specific application"
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
            usage = context.services.application.resources.get_cpu_usage(app_name)
            return ActionResult(success=True, data={"cpu_percent": usage})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetApplicationMemoryUsage(Action):
    name = "get_application_memory_usage"
    description = "Get the current memory consumption (RAM) for a specific application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            mem_data = context.services.application.resources.get_memory_usage(app_name)
            return ActionResult(success=True, data={
                "memory_bytes": mem_data.get("bytes"),
                "memory_mb": mem_data.get("mb")
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetApplicationDiskUsage(Action):
    name = "get_application_disk_usage"
    description = "Get the disk I/O (read/write) activity for a specific application"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            disk_data = context.services.application.resources.get_disk_usage(app_name)
            return ActionResult(success=True, data={
                "read_bytes": disk_data.get("read_bytes"),
                "write_bytes": disk_data.get("write_bytes")
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetApplicationResourceUsage(Action):
    name = "get_application_resource_usage"
    description = "Get an aggregated report of CPU, Memory, and Disk usage for an application"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            usage = context.services.application.resources.get_resource_usage(app_name)
            return ActionResult(success=True, data=usage)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetTopResourceApplications(Action):
    name = "get_top_resource_applications"
    description = "Identify which applications are consuming the most resources (CPU or Memory)"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "resource": {
            "type": "string",
            "required": True,
            "enum": ["cpu", "memory"],
            "description": "Type of resource to monitor"
        },
        "limit": {
            "type": "integer",
            "required": False,
            "default": 10,
            "description": "Number of applications to return"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        resource_type = params.get('resource')
        limit = params.get('limit', 10)

        if not resource_type:
            return ActionResult(success=False, error="Parameter 'resource' is required", error_code="MISSING_PARAM")

        try:
            apps = context.services.application.resources.get_top_resource_apps(resource_type, limit)
            return ActionResult(success=True, data={
                "resource": resource_type,
                "applications": apps
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")