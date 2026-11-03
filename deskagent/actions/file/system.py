from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


def _get_service(context):
    if hasattr(context, "services"):
        if hasattr(context.services, "system") and hasattr(context.services.system, "file"):
            return context.services.system.file
        if hasattr(context.services, "file") and hasattr(context.services.file, "system"):
            return context.services.file.system
        if hasattr(context.services, "file"):
            return context.services.file
    return None


class OpenFile(Action):
    name = "open_file"
    description = "Open a file using the system default application"
    category = ActionCategory.FILE
    risk_level = RiskLevel.LOW
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = (parameters or {}).get("path")
        try:
            srv = _get_service(context)
            if hasattr(srv, "open_file"):
                srv.open_file(path)
            else:
                srv.open(path)
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
        "application": {"type": "string", "required": True},
    }

    def execute(self, context, parameters):
        p = parameters or {}
        path, app = p.get("path"), p.get("application")
        try:
            srv = _get_service(context)
            if hasattr(srv, "open_file_with_application"):
                srv.open_file_with_application(path, app)
            else:
                srv.open_with(path, app)
            return ActionResult(success=True, data={"opened": True, "path": path, "application": app})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RevealFile(Action):
    name = "reveal_file"
    description = "Open the file manager and highlight the file/directory"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = (parameters or {}).get("path")
        try:
            srv = _get_service(context)
            if hasattr(srv, "reveal_file"):
                srv.reveal_file(path)
            else:
                srv.reveal(path)
            return ActionResult(success=True, data={"revealed": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RevealFileInFileManager(RevealFile):
    name = "reveal_file_in_file_manager"
    description = "Reveal a file in Finder"

    def execute(self, context, parameters):
        path = (parameters or {}).get("path")
        try:
            srv = _get_service(context)
            if hasattr(srv, "reveal_file_in_file_manager"):
                srv.reveal_file_in_file_manager(path)
            elif hasattr(srv, "reveal_file"):
                srv.reveal_file(path)
            else:
                srv.reveal(path)
            return ActionResult(success=True, data={"revealed": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileDefaultApplication(Action):
    name = "get_file_default_application"
    description = "Get the name of the default application assigned to this file type"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = (parameters or {}).get("path")
        try:
            srv = _get_service(context)
            if hasattr(srv, "get_default_application"):
                app_name = srv.get_default_application(path)
            else:
                app_name = srv.get_default_app(path)
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
        "application": {"type": "string", "required": True},
    }

    def execute(self, context, parameters):
        p = parameters or {}
        path, app = p.get("path"), p.get("application")
        try:
            srv = _get_service(context)
            if hasattr(srv, "set_default_application"):
                srv.set_default_application(path, app)
            else:
                srv.set_default_app(path, app)
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
        path = (parameters or {}).get("path")
        try:
            srv = _get_service(context)
            if hasattr(srv, "lock_file"):
                srv.lock_file(path)
            else:
                srv.lock(path)
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
        path = (parameters or {}).get("path")
        try:
            srv = _get_service(context)
            if hasattr(srv, "unlock_file"):
                srv.unlock_file(path)
            else:
                srv.unlock(path)
            return ActionResult(success=True, data={"unlocked": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetFileLockState(Action):
    name = "get_file_lock_state"
    description = "Check if the file has the system 'Locked' flag enabled"
    category = ActionCategory.FILE
    parameters_schema = {"path": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        path = (parameters or {}).get("path")
        try:
            srv = _get_service(context)
            if hasattr(srv, "get_file_lock_state"):
                is_locked = srv.get_file_lock_state(path)
            else:
                is_locked = srv.is_locked(path)
            return ActionResult(success=True, data={"locked": is_locked})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))
