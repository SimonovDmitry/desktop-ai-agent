from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


class GetApplicationCPUUsage(Action):
    name = "get_application_cpu_usage"
    description = "Get the current CPU usage percentage for a specific application"
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
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            mem_data = context.services.application.resources.get_memory_usage(app_name)
            res = {}
            if isinstance(mem_data, dict):
                res["memory_bytes"] = mem_data.get("memory_bytes", mem_data.get("bytes"))
                res["memory_mb"] = mem_data.get("memory_mb", mem_data.get("mb"))
            else:
                res["memory_bytes"] = mem_data
                res["memory_mb"] = round(mem_data / (1024 * 1024), 2)
            return ActionResult(success=True, data=res)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetApplicationDiskUsage(Action):
    name = "get_application_disk_usage"
    description = "Get the disk I/O (read/write) activity for a specific application"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            disk_data = context.services.application.resources.get_disk_usage(app_name)
            return ActionResult(success=True, data=disk_data)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetApplicationResourceUsage(Action):
    name = "get_application_resource_usage"
    description = "Get an aggregated report of CPU, Memory, and Disk usage for an application"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get("application")
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            usage = context.services.application.resources.get_resource_usage(app_name)
            return ActionResult(success=True, data=usage)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


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
            "description": "Type of resource to monitor",
        },
        "limit": {
            "type": "integer",
            "required": False,
            "default": 10,
            "description": "Number of applications to return",
        },
    }

    def execute(self, context, parameters):
        params = parameters or {}
        if "resource" not in params:
            return ActionResult(success=False, error="Parameter 'resource' is required", error_code="MISSING_PARAM")

        resource_type = params.get("resource")
        if resource_type not in ("cpu", "memory"):
            return ActionResult(
                success=False,
                error="Invalid resource. Must be 'cpu' or 'memory'",
                error_code="INVALID_INPUT",
            )

        limit = params.get("limit", 10)
        if not isinstance(limit, int) or limit <= 0:
            return ActionResult(
                success=False,
                error="Limit must be a positive integer",
                error_code="INVALID_INPUT",
            )

        try:
            srv = context.services.application.resources
            if hasattr(srv, "get_top_resource_applications"):
                apps = srv.get_top_resource_applications(resource_type, limit)
            else:
                apps = srv.get_top_resource_apps(resource_type, limit)
            return ActionResult(success=True, data={"resource": resource_type, "applications": apps})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
