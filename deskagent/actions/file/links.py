from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class CreateSymbolicLink(Action):
    name = "create_symbolic_link"
    description = "Create a symbolic link (shortcut) pointing to a target file or directory"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "target": {"type": "string", "required": True, "description": "Original file/folder path"},
        "link": {"type": "string", "required": True, "description": "Path where the link will be created"}
    }

    def execute(self, context, parameters):
        target, link = parameters.get('target'), parameters.get('link')
        try:
            context.services.file.links.create_symlink(target, link)
            return ActionResult(success=True, data={"created": True, "link": link, "target": target})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class CreateHardLink(Action):
    name = "create_hard_link"
    description = "Create a hard link to a file (pointing to the same inode)"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "target": {"type": "string", "required": True},
        "link": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        target, link = parameters.get('target'), parameters.get('link')
        try:
            context.services.file.links.create_hardlink(target, link)
            return ActionResult(success=True, data={"created": True, "link": link, "target": target})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ReadSymbolicLink(Action):
    name = "read_symbolic_link"
    description = "Read the immediate target path that a symbolic link points to"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            target = context.services.file.links.read_symlink(path)
            return ActionResult(success=True, data={"link": path, "target": target})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetLinkTarget(Action):
    name = "get_link_target"
    description = "Recursively follow links to find the final real file or directory"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            real_target = context.services.file.links.get_final_target(path)
            return ActionResult(success=True, data={"path": path, "real_target": real_target})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ResolvePath(Action):
    name = "resolve_path"
    description = "Expand home directory (~), resolve all symlinks, and return an absolute normalized path"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            resolved = context.services.file.links.resolve_full_path(path)
            return ActionResult(success=True, data={"input": path, "resolved": resolved})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RemoveLink(Action):
    name = "remove_link"
    description = "Remove a link file without affecting the original target"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            context.services.file.links.remove_link(path)
            return ActionResult(success=True, data={"link_removed": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))