from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetApplicationPermissions(Action):
    name = "get_application_permissions"
    description = "Get all available system permissions for a specific application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "application": {
            "type": "string",
            "required": True,
            "description": "Name of the application to check"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        if not app_name:
            return ActionResult(success=False, error="Parameter 'application' is required", error_code="MISSING_PARAM")

        try:
            permissions = context.services.application.preferences.get_permissions(app_name)
            return ActionResult(success=True, data={"permissions": permissions})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetAccessibilityPermission(Action):
    name = "get_accessibility_permission"
    description = "Check if the application has Accessibility (UI Automation) permission"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            granted = context.services.application.preferences.get_accessibility_status(app_name)
            return ActionResult(success=True, data={"granted": granted})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetAutomationPermission(Action):
    name = "get_automation_permission"
    description = "Check if the application has AppleEvents/Automation permission"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            granted = context.services.application.preferences.get_automation_status(app_name)
            return ActionResult(success=True, data={"granted": granted})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetNotificationPermission(Action):
    name = "get_notification_permission"
    description = "Check if the application is allowed to send system notifications"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            granted = context.services.application.preferences.get_notification_status(app_name)
            return ActionResult(success=True, data={"granted": granted})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetDefaultApplication(Action):
    name = "get_default_application"
    description = "Find which application is set as default for a specific file type"
    category = ActionCategory.APPLICATION
    parameters_schema = {
        "file_type": {
            "type": "string",
            "required": True,
            "description": "File extension (e.g. '.pdf') or UTI"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        file_type = params.get('file_type')
        if not file_type: return ActionResult(success=False, error="Missing file_type")

        try:
            app_name = context.services.application.preferences.get_default_app(file_type)
            return ActionResult(success=True, data={"file_type": file_type, "application": app_name})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class OpenWithApplication(Action):
    name = "open_with_application"
    description = "Open a specific file using a chosen application"
    category = ActionCategory.APPLICATION
    parameters_schema = {
        "path": {"type": "string", "required": True},
        "application": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        params = parameters or {}
        path = params.get('path')
        app_name = params.get('application')
        if not path or not app_name: return ActionResult(success=False, error="Missing path or application")

        try:
            context.services.application.preferences.open_with(path, app_name)
            return ActionResult(success=True, data={"opened": True, "path": path, "application": app_name})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class OpenApplicationPreferences(Action):
    name = "open_application_preferences"
    description = "Open the internal preferences/settings window of a specific application"
    category = ActionCategory.APPLICATION
    parameters_schema = {"application": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        try:
            context.services.application.preferences.open_app_prefs(app_name)
            return ActionResult(success=True, data={"opened": True, "application": app_name})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class OpenApplicationSystemSettings(Action):
    name = "open_application_system_settings"
    description = "Open OS System Settings (Privacy, Security, etc.) related to an application"
    category = ActionCategory.APPLICATION
    parameters_schema = {
        "application": {"type": "string", "required": True},
        "section": {
            "type": "string",
            "required": True,
            "enum": ["accessibility", "automation", "notifications", "general"],
            "description": "System settings section to open"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        section = params.get('section')
        if not app_name or not section: return ActionResult(success=False, error="Missing parameters")

        try:
            context.services.application.preferences.open_system_settings(app_name, section)
            return ActionResult(success=True, data={"opened": True, "section": section})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))