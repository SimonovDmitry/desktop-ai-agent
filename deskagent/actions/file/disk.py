from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


class GetFileDiskUsage(Action):
    name = "get_file_disk_usage"
    description = "Get the actual space a file occupies on the disk (blocks used)"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = (parameters or {}).get("path") or (parameters or {}).get("file")
        try:
            usage = context.services.file.disk.get_file_usage(path)
            return ActionResult(
                success=True,
                data={"path": path, "size": usage, "disk_usage": usage, "disk_usage_bytes": usage},
            )
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetDirectoryDiskUsage(Action):
    name = "get_directory_disk_usage"
    description = "Recursively calculate the total size of all files inside a directory"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = (parameters or {}).get("path") or (parameters or {}).get("directory")
        try:
            usage_data = context.services.file.disk.get_directory_usage(path)
            size = usage_data.get("size", 0)
            return ActionResult(
                success=True,
                data={
                    "path": path,
                    "size": size,
                    "disk_usage": size,
                    "total_size": size,
                    "file_count": usage_data.get("files", 0),
                    "directory_count": usage_data.get("directories", 0),
                },
            )
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetDiskUsage(Action):
    name = "get_disk_usage"
    description = "Get total, used, and free space for the entire filesystem or drive"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": False, "default": "/", "description": "Any path on the target partition"}
    }

    def execute(self, context, parameters):
        path = (parameters or {}).get("path") or (parameters or {}).get("directory") or "/"
        try:
            usage = context.services.file.disk.get_system_usage(path)
            return ActionResult(success=True, data=usage)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FindLargestFiles(Action):
    name = "find_largest_files"
    description = "Search for the biggest files within a specific directory"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "limit": {"type": "integer", "required": False, "default": 10},
        "recursive": {"type": "boolean", "required": False, "default": True},
    }

    def execute(self, context, parameters):
        p = parameters or {}
        path = p.get("path") or p.get("directory")
        limit = p.get("limit", 10)
        recursive = p.get("recursive", True)
        try:
            files = context.services.file.disk.find_largest_files(path, limit, recursive)
            return ActionResult(
                success=True,
                data={"files": files, "results": files, "largest_files": files},
            )
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FindLargestDirectories(Action):
    name = "find_largest_directories"
    description = "Search for directories that consume the most space"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "limit": {"type": "integer", "required": False, "default": 5},
    }

    def execute(self, context, parameters):
        p = parameters or {}
        path = p.get("path") or p.get("directory")
        limit = p.get("limit", 5)
        try:
            dirs = context.services.file.disk.find_largest_directories(path, limit)
            return ActionResult(
                success=True,
                data={"directories": dirs, "results": dirs, "largest_directories": dirs},
            )
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetStorageStatistics(Action):
    name = "get_storage_statistics"
    description = "Generate a comprehensive report of disk health and storage distribution"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": False, "default": "/"}}

    def execute(self, context, parameters):
        p = parameters or {}
        path = p.get("path") or p.get("directory") or "/"
        try:
            stats = context.services.file.disk.get_statistics(path)
            data = {}
            if isinstance(stats, dict):
                if "disk" in stats and isinstance(stats["disk"], dict):
                    data.update(stats["disk"])
                data.update(stats)
            if "percent" in data and "usage_percent" not in data:
                data["usage_percent"] = data["percent"]
            return ActionResult(success=True, data=data)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))
