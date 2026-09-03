from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class OpenFile(Action):
    name = "open_file"
    description = "Open a file using the system default application"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            context.services.file.system.open(path)
            return ActionResult(success=True, data={"opened": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class OpenFileWithApplication(Action):
    name = "open_file_with_application"
    description = "Open a file using a specific application"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "application": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        path, app = parameters.get('path'), parameters.get('application')
        try:
            context.services.file.system.open_with(path, app)
            return ActionResult(success=True, data={"opened": True, "path": path, "application": app})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RevealFile(Action):
    name = "reveal_file"
    description = "Open the file manager and highlight the file/directory"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            context.services.file.system.reveal(path)
            return ActionResult(success=True, data={"revealed": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileDefaultApplication(Action):
    name = "get_file_default_application"
    description = "Get the name of the default application assigned to this file type"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            app_name = context.services.file.system.get_default_app(path)
            return ActionResult(success=True, data={"application": app_name})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SetFileDefaultApplication(Action):
    name = "set_file_default_application"
    description = "Change the default application for this file type (System-wide change)"
    category = ActionCategory.FILE
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "application": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        path, app = parameters.get('path'), parameters.get('application')
        try:
            context.services.file.system.set_default_app(path, app)
            return ActionResult(success=True, data={"updated": True, "new_default": app})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class LockFile(Action):
    name = "lock_file"
    description = "Set the system 'Locked' flag on a file (prevents modification/deletion)"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            context.services.file.system.lock(path)
            return ActionResult(success=True, data={"locked": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class UnlockFile(Action):
    name = "unlock_file"
    description = "Remove the system 'Locked' flag from a file"
    category = ActionCategory.FILE
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            context.services.file.system.unlock(path)
            return ActionResult(success=True, data={"unlocked": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileLockState(Action):
    name = "get_file_lock_state"
    description = "Check if the file has the system 'Locked' flag enabled"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = parameters.get('path')
        try:
            is_locked = context.services.file.system.is_locked(path)
            return ActionResult(success=True, data={"locked": is_locked})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))