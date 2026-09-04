from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class FindFiles(Action):
    name = "find_files"
    description = "Universal search for files using patterns and recursion"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "pattern": {"type": "string", "required": False, "default": "*"},
        "recursive": {"type": "boolean", "required": False, "default": True}
    }

    def execute(self, context, parameters):
        dir_path = parameters.get('directory')
        pattern = parameters.get('pattern', '*')
        recursive = parameters.get('recursive', True)
        try:
            files = context.services.file.search.find(dir_path, pattern, recursive)
            return ActionResult(success=True, data={"files": files, "count": len(files)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FindFilesByName(Action):
    name = "find_files_by_name"
    description = "Find files with a specific name"
    category = ActionCategory.FILE
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "name": {"type": "string", "required": True},
        "recursive": {"type": "boolean", "required": False, "default": True}
    }

    def execute(self, context, parameters):
        d, n = parameters.get('directory'), parameters.get('name')
        rec = parameters.get('recursive', True)
        try:
            files = context.services.file.search.find_by_name(d, n, rec)
            return ActionResult(success=True, data={"files": files, "count": len(files)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FindFilesByExtension(Action):
    name = "find_files_by_extension"
    description = "Find files with specific extensions (e.g., .pdf, .jpg)"
    category = ActionCategory.FILE
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "extension": {"type": "string", "required": True},
        "recursive": {"type": "boolean", "required": False, "default": True}
    }

    def execute(self, context, parameters):
        d, ext = parameters.get('directory'), parameters.get('extension')
        rec = parameters.get('recursive', True)
        try:
            files = context.services.file.search.find_by_extension(d, ext, rec)
            return ActionResult(success=True, data={"files": files, "count": len(files)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FindFilesByType(Action):
    name = "find_files_by_type"
    description = "Find files by category (image, document, video, archive, etc.)"
    category = ActionCategory.FILE
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "type": {"type": "string", "required": True, "enum": ["image", "document", "video", "audio", "archive", "code"]},
        "recursive": {"type": "boolean", "required": False, "default": True}
    }

    def execute(self, context, parameters):
        d, t = parameters.get('directory'), parameters.get('type')
        rec = parameters.get('recursive', True)
        try:
            files = context.services.file.search.find_by_type(d, t, rec)
            return ActionResult(success=True, data={"files": files, "count": len(files)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FindFilesBySize(Action):
    name = "find_files_by_size"
    description = "Find files within a specific size range (in bytes)"
    category = ActionCategory.FILE
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "min_size": {"type": "integer", "required": False},
        "max_size": {"type": "integer", "required": False},
        "recursive": {"type": "boolean", "required": False, "default": True}
    }

    def execute(self, context, parameters):
        p = parameters
        try:
            files = context.services.file.search.find_by_size(p['directory'], p.get('min_size'), p.get('max_size'), p.get('recursive', True))
            return ActionResult(success=True, data={"files": files, "count": len(files)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FindFilesByDate(Action):
    name = "find_files_by_date"
    description = "Find files modified within a date range"
    category = ActionCategory.FILE
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "modified_after": {"type": "string", "required": False, "description": "ISO date string"},
        "modified_before": {"type": "string", "required": False, "description": "ISO date string"},
        "recursive": {"type": "boolean", "required": False, "default": True}
    }

    def execute(self, context, parameters):
        p = parameters
        try:
            files = context.services.file.search.find_by_date(p['directory'], p.get('modified_after'), p.get('modified_before'), p.get('recursive', True))
            return ActionResult(success=True, data={"files": files, "count": len(files)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FindFilesByContent(Action):
    name = "find_files_by_content"
    description = "Grep-like search: find text strings inside files"
    category = ActionCategory.FILE
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "query": {"type": "string", "required": True},
        "extensions": {"type": "list", "required": False},
        "recursive": {"type": "boolean", "required": False, "default": True}
    }

    def execute(self, context, parameters):
        p = parameters
        try:
            results = context.services.file.search.find_by_content(p['directory'], p['query'], p.get('extensions'), p.get('recursive', True))
            return ActionResult(success=True, data={"matches": results, "count": len(results)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FindRecentFiles(Action):
    name = "find_recent_files"
    description = "Get files modified in the last N days"
    category = ActionCategory.FILE
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "days": {"type": "integer", "required": False, "default": 7}
    }

    def execute(self, context, parameters):
        d, days = parameters.get('directory'), parameters.get('days', 7)
        try:
            files = context.services.file.search.get_recent(d, days)
            return ActionResult(success=True, data={"files": files, "count": len(files)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FindLargeFiles(Action):
    name = "find_large_files"
    description = "Find top N largest files in a directory"
    category = ActionCategory.FILE
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "limit": {"type": "integer", "required": False, "default": 20}
    }

    def execute(self, context, parameters):
        d, limit = parameters.get('directory'), parameters.get('limit', 20)
        try:
            files = context.services.file.search.get_largest(d, limit)
            return ActionResult(success=True, data={"files": files})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class FindDuplicateFiles(Action):
    name = "find_duplicate_files"
    description = "Identify identical files by calculating content hashes"
    category = ActionCategory.FILE
    parameters_schema = {
        "directory": {"type": "string", "required": True},
        "recursive": {"type": "boolean", "required": False, "default": True}
    }

    def execute(self, context, parameters):
        d, rec = parameters.get('directory'), parameters.get('recursive', True)
        try:
            duplicates = context.services.file.search.find_duplicates(d, rec)
            return ActionResult(success=True, data={"duplicates": duplicates})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))