from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class OpenDocument(Action):
    name = "open_document"
    description = "Open a file using the system default application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "path": {
            "type": "string",
            "required": True,
            "description": "Full path to the document/file"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        path = params.get('path')
        if not path:
            return ActionResult(success=False, error="Parameter 'path' is required", error_code="MISSING_PARAM")

        try:
            context.services.application.documents.open(path)
            return ActionResult(success=True, data={"opened": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class OpenMultipleDocuments(Action):
    name = "open_multiple_documents"
    description = "Open several files simultaneously using their default applications"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "paths": {
            "type": "list",
            "required": True,
            "description": "List of full paths to files"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        paths = params.get('paths')
        if not isinstance(paths, list):
            return ActionResult(success=False, error="Parameter 'paths' must be a list", error_code="INVALID_INPUT")

        try:
            context.services.application.documents.open_multiple(paths)
            return ActionResult(success=True, data={"opened": paths, "count": len(paths)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class OpenURLWithApplication(Action):
    name = "open_url_with_application"
    description = "Open a specific URL (link) using a chosen application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "url": {"type": "string", "required": True, "description": "The URL to open"},
        "application": {"type": "string", "required": True, "description": "App name (e.g., 'Safari')"}
    }

    def execute(self, context, parameters):
        params = parameters or {}
        url = params.get('url')
        app_name = params.get('application')
        if not url or not app_name:
            return ActionResult(success=False, error="URL and Application are required", error_code="MISSING_PARAM")

        try:
            context.services.application.documents.open_url_with(url, app_name)
            return ActionResult(success=True, data={"opened": True, "url": url, "application": app_name})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class RevealApplicationInFileManager(Action):
    name = "reveal_application_in_file_manager"
    description = "Open the file manager and highlight the application bundle (.app)"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            path = context.services.application.documents.reveal_app(app_name)
            return ActionResult(success=True, data={"revealed": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RevealApplicationExecutable(Action):
    name = "reveal_application_executable"
    description = "Open the file manager and highlight the actual binary executable of an app"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            path = context.services.application.documents.reveal_executable(app_name)
            return ActionResult(success=True, data={"revealed": True, "path": path})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))