from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class CreateTemporaryFile(Action):
    name = "create_temporary_file"
    description = "Create a unique temporary file that will exist until it is deleted or the system reboots"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "prefix": {"type": "string", "required": False, "default": "agent_"},
        "suffix": {"type": "string", "required": False, "default": ".tmp"},
        "content": {"type": "string", "required": False}
    }

    def execute(self, context, parameters):
        p = parameters
        try:
            path = context.services.file.temporary.create_file(
                prefix=p.get('prefix', 'agent_'),
                suffix=p.get('suffix', '.tmp'),
                content=p.get('content')
            )
            return ActionResult(success=True, data={"path": path, "created": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class CreateTemporaryDirectory(Action):
    name = "create_temporary_directory"
    description = "Create a unique temporary directory for a batch of files"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "prefix": {"type": "string", "required": False, "default": "agent_dir_"}
    }

    def execute(self, context, parameters):
        prefix = parameters.get('prefix', 'agent_dir_')
        try:
            path = context.services.file.temporary.create_directory(prefix=prefix)
            return ActionResult(success=True, data={"path": path, "created": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetTemporaryDirectory(Action):
    name = "get_temporary_directory"
    description = "Get the standard system path for temporary files"
    category = ActionCategory.FILE
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            path = context.services.file.temporary.get_system_temp_path()
            return ActionResult(success=True, data={"path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class CleanupTemporaryFile(Action):
    name = "cleanup_temporary_file"
    description = "Remove a specific temporary file"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            context.services.file.temporary.delete_file(path)
            return ActionResult(success=True, data={"deleted": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class CleanupTemporaryDirectory(Action):
    name = "cleanup_temporary_directory"
    description = "Recursively remove a temporary directory and its contents"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            context.services.file.temporary.delete_directory(path)
            return ActionResult(success=True, data={"deleted": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class CleanupTemporaryFiles(Action):
    name = "cleanup_temporary_files"
    description = "Bulk remove all temporary files created by the agent in this session"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "prefix": {"type": "string", "required": False, "default": "agent_"}
    }

    def execute(self, context, parameters):
        prefix = parameters.get('prefix', 'agent_')
        try:
            count = context.services.file.temporary.cleanup_all(prefix=prefix)
            return ActionResult(success=True, data={"cleaned_count": count, "prefix_used": prefix})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))