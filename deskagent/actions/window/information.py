from deskagent.core.action import Action, ActionResult, ActionCategory, RiskLevel


class GetWindows(Action):
    name = "get_windows"
    description = "Get a list of all open windows, optionally filtered by application or visibility"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "application": {
            "type": "string",
            "required": False,
            "description": "Filter windows by application name (e.g., 'Safari')"
        },
        "visible_only": {
            "type": "boolean",
            "required": False,
            "default": True,
            "description": "If true, returns only windows that are currently visible"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        app_name = params.get('application')
        visible_only = params.get('visible_only', True)

        try:
            windows = context.services.window.information.get_windows(
                application=app_name,
                visible_only=visible_only
            )
            return ActionResult(success=True, data={"windows": windows, "count": len(windows)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetWindow(Action):
    name = "get_window"
    description = "Get detailed information about a specific window by its ID"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {
            "type": "integer",
            "required": True,
            "description": "The unique identifier of the window"
        }
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            info = context.services.window.information.get_window_info(win_id)
            if not info:
                return ActionResult(success=False, error=f"Window with ID {win_id} not found", error_code="NOT_FOUND")
            return ActionResult(success=True, data=info)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class FindWindows(Action):
    name = "find_windows"
    description = "Search for windows by title or application name"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "title": {"type": "string", "required": False},
        "title_contains": {"type": "string", "required": False},
        "application": {"type": "string", "required": False}
    }

    def execute(self, context, parameters):
        try:
            windows = context.services.window.information.find_windows(
                title=parameters.get('title'),
                title_contains=parameters.get('title_contains'),
                application=parameters.get('application')
            )
            return ActionResult(success=True, data={"windows": windows, "count": len(windows)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetActiveWindow(Action):
    name = "get_active_window"
    description = "Get information about the currently focused window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            window = context.services.window.information.get_active_window()
            return ActionResult(success=True, data=window)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetWindowBounds(Action):
    name = "get_window_bounds"
    description = "Get the position and size of a specific window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            bounds = context.services.window.information.get_window_bounds(win_id)
            return ActionResult(success=True, data=bounds)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetWindowState(Action):
    name = "get_window_state"
    description = "Get the state of a window (normal, minimized, maximized, etc.)"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            state = context.services.window.information.get_window_state(win_id)
            return ActionResult(success=True, data={"state": state})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetWindowApplication(Action):
    name = "get_window_application"
    description = "Get the application name and PID associated with a window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            app_info = context.services.window.information.get_window_application(win_id)
            return ActionResult(success=True, data=app_info)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class IsWindowVisible(Action):
    name = "is_window_visible"
    description = "Check if a specific window is currently visible"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            visible = context.services.window.information.is_window_visible(win_id)
            return ActionResult(success=True, data={"visible": visible})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")