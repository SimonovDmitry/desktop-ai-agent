from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetFilePermissions(Action):
    name = "get_file_permissions"
    description = "Get detailed information about file mode and access rights"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            perms = context.services.file.permissions.get_permissions(path)
            return ActionResult(success=True, data=perms)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileOwner(Action):
    name = "get_file_owner"
    description = "Get the owner name of the file or directory"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            owner = context.services.file.permissions.get_owner(path)
            return ActionResult(success=True, data={"owner": owner})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileGroup(Action):
    name = "get_file_group"
    description = "Get the group name associated with the file"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            group = context.services.file.permissions.get_group(path)
            return ActionResult(success=True, data={"group": group})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SetFilePermissions(Action):
    name = "set_file_permissions"
    description = "Set file permissions using octal mode (e.g., '0755')"
    category = ActionCategory.FILE
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "mode": {"type": "string", "required": True, "description": "Octal mode like '0644'"}
    }

    def execute(self, context, parameters):
        path, mode = parameters.get('path'), parameters.get('mode')
        try:
            context.services.file.permissions.set_permissions(path, mode)
            return ActionResult(success=True, data={"path": path, "new_mode": mode})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class AddFilePermission(Action):
    name = "add_file_permission"
    description = "Add a specific permission (read, write, or execute) to a file"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "target": {"type": "string", "required": True, "enum": ["owner", "group", "others"]},
        "permission": {"type": "string", "required": True, "enum": ["read", "write", "execute"]}
    }

    def execute(self, context, parameters):
        p = parameters
        try:
            context.services.file.permissions.add_permission(p['path'], p['target'], p['permission'])
            return ActionResult(success=True, data={"status": "added", "permission": p['permission']})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RemoveFilePermission(Action):
    name = "remove_file_permission"
    description = "Remove a specific permission from a file"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "target": {"type": "string", "required": True, "enum": ["owner", "group", "others"]},
        "permission": {"type": "string", "required": True, "enum": ["read", "write", "execute"]}
    }

    def execute(self, context, parameters):
        p = parameters
        try:
            context.services.file.permissions.remove_permission(p['path'], p['target'], p['permission'])
            return ActionResult(success=True, data={"status": "removed", "permission": p['permission']})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SetFileOwner(Action):
    name = "set_file_owner"
    description = "Change the owner of a file (requires administrative privileges)"
    category = ActionCategory.FILE
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "owner": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        path, owner = parameters.get('path'), parameters.get('owner')
        try:
            context.services.file.permissions.set_owner(path, owner)
            return ActionResult(success=True, data={"path": path, "new_owner": owner})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SetFileGroup(Action):
    name = "set_file_group"
    description = "Change the group of a file"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "group": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        path, group = parameters.get('path'), parameters.get('group')
        try:
            context.services.file.permissions.set_group(path, group)
            return ActionResult(success=True, data={"path": path, "new_group": group})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsFileReadable(Action):
    name = "is_file_readable"
    description = "Check if the current process has read access to the file"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            result = context.services.file.permissions.can_read(path)
            return ActionResult(success=True, data={"readable": result})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsFileWritable(Action):
    name = "is_file_writable"
    description = "Check if the current process has write access to the file"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            result = context.services.file.permissions.can_write(path)
            return ActionResult(success=True, data={"writable": result})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsFileExecutable(Action):
    name = "is_file_executable"
    description = "Check if the file can be executed as a program or script"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            result = context.services.file.permissions.can_execute(path)
            return ActionResult(success=True, data={"executable": result})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))