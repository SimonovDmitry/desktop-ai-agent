from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory

class CreateFile(Action):
    name = "create_file"
    description = "Create a new file with optional content"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "content": {"type": "string", "required": False, "default": ""}
    }

    def execute(self, context, parameters):
        path = parameters.get('path')
        content = parameters.get('content', "")
        try:
            result = context.services.file.lifecycle.create(path, content)
            return ActionResult(success=True, data={
                "created": True,
                "path": path,
                "size": len(content)
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class DeleteFile(Action):
    name = "delete_file"
    description = "Permanently delete a file from the system"
    category = ActionCategory.FILE
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            context.services.file.lifecycle.delete(path)
            return ActionResult(success=True, data={"deleted": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class TrashFile(Action):
    name = "trash_file"
    description = "Move a file to the Trash/Recycle Bin (safer than delete)"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            context.services.file.lifecycle.move_to_trash(path)
            return ActionResult(success=True, data={"trashed": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RestoreFile(Action):
    name = "restore_file"
    description = "Restore a file from the Trash/Recycle Bin"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            context.services.file.lifecycle.restore(path)
            return ActionResult(success=True, data={"restored": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class EmptyTrash(Action):
    name = "empty_trash"
    description = "Permanently clear all items in the Trash"
    category = ActionCategory.FILE
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.file.lifecycle.empty_trash()
            return ActionResult(success=True, data={"empty": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RenameFile(Action):
    name = "rename_file"
    description = "Change the name of a file or directory"
    category = ActionCategory.FILE
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "new_name": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        path = parameters.get('path')
        new_name = parameters.get('new_name')
        try:
            new_path = context.services.file.lifecycle.rename(path, new_name)
            return ActionResult(success=True, data={
                "renamed": True,
                "old_path": path,
                "new_path": new_path
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class CopyFile(Action):
    name = "copy_file"
    description = "Copy a file from source to destination"
    category = ActionCategory.FILE
    parameters_schema = {
        "source": {"type": "string", "required": True},
        "destination": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        src, dst = parameters.get('source'), parameters.get('destination')
        try:
            context.services.file.lifecycle.copy(src, dst)
            return ActionResult(success=True, data={"copied": True, "source": src, "destination": dst})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class MoveFile(Action):
    name = "move_file"
    description = "Move a file from source to destination"
    category = ActionCategory.FILE
    parameters_schema = {
        "source": {"type": "string", "required": True},
        "destination": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        src, dst = parameters.get('source'), parameters.get('destination')
        try:
            context.services.file.lifecycle.move(src, dst)
            return ActionResult(success=True, data={"moved": True, "source": src, "destination": dst})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class DuplicateFile(Action):
    name = "duplicate_file"
    description = "Create a copy of a file in the same directory with a new name"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            new_path = context.services.file.lifecycle.duplicate(path)
            return ActionResult(success=True, data={"duplicated": True, "source": path, "destination": new_path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ReplaceFile(Action):
    name = "replace_file"
    description = "Replace one file with another file's content/identity"
    category = ActionCategory.FILE
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    parameters_schema = {
        "target_path": {"type": "string", "required": True},
        "source_path": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        target, source = parameters.get('target_path'), parameters.get('source_path')
        try:
            context.services.file.lifecycle.replace(target, source)
            return ActionResult(success=True, data={"replaced": True, "target": target})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))