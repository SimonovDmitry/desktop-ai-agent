from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class CloseWindow(Action):
    name = "close_window"
    description = "Close a specific window by its ID"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    reversible = False
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window to close"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.lifecycle.close(win_id)
            return ActionResult(success=True, data={"closed": True, "window_id": win_id})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class CloseWindows(Action):
    name = "close_windows"
    description = "Close multiple specific windows at once"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    reversible = False
    parameters_schema = {
        "window_ids": {"type": "list", "required": True, "description": "List of window IDs to close"}
    }

    def execute(self, context, parameters):
        win_ids = parameters.get('window_ids')
        try:
            results = context.services.window.lifecycle.close_multiple(win_ids)
            return ActionResult(success=True, data=results)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class CloseApplicationWindows(Action):
    name = "close_application_windows"
    description = "Close all windows belonging to a specific application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True
    reversible = False
    parameters_schema = {
        "application": {"type": "string", "required": True, "description": "Name of the application"}
    }

    def execute(self, context, parameters):
        app_name = parameters.get('application')
        try:
            count = context.services.window.lifecycle.close_app_windows(app_name)
            return ActionResult(success=True, data={"application": app_name, "closed_count": count})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class WaitForWindow(Action):
    name = "wait_for_window"
    description = "Wait for a window with a specific title to appear"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "title": {"type": "string", "required": True, "description": "Title or partial title to wait for"},
        "timeout": {"type": "integer", "required": False, "default": 10, "description": "Seconds to wait"}
    }

    def execute(self, context, parameters):
        title = parameters.get('title')
        timeout = parameters.get('timeout', 10)
        try:
            window_info = context.services.window.lifecycle.wait_for_window(title, timeout)
            return ActionResult(success=True, data={"found": True, "window": window_info})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="TIMEOUT")


class WaitForWindowClose(Action):
    name = "wait_for_window_close"
    description = "Wait until a specific window is closed or disappears"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_id": {"type": "integer", "required": True},
        "timeout": {"type": "integer", "required": False, "default": 10}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        timeout = parameters.get('timeout', 10)
        try:
            context.services.window.lifecycle.wait_for_close(win_id, timeout)
            return ActionResult(success=True, data={"closed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="TIMEOUT")


class WaitForWindowVisible(Action):
    name = "wait_for_window_visible"
    description = "Wait until a specific window becomes visible on the screen"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_id": {"type": "integer", "required": True},
        "timeout": {"type": "integer", "required": False, "default": 10}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        timeout = parameters.get('timeout', 10)
        try:
            context.services.window.lifecycle.wait_for_visibility(win_id, timeout, visible=True)
            return ActionResult(success=True, data={"visible": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="TIMEOUT")


class WaitForWindowActive(Action):
    name = "wait_for_window_active"
    description = "Wait until a specific window becomes focused/active"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_id": {"type": "integer", "required": True},
        "timeout": {"type": "integer", "required": False, "default": 10}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        timeout = parameters.get('timeout', 10)
        try:
            context.services.window.lifecycle.wait_for_active(win_id, timeout)
            return ActionResult(success=True, data={"active": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="TIMEOUT")
