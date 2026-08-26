from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class ArrangeWindows(Action):
    name = "arrange_windows"
    description = "Arrange multiple windows in a specific layout (horizontal or vertical)"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_ids": {"type": "list", "required": True, "description": "List of window IDs to arrange"},
        "layout": {"type": "string", "required": True, "enum": ["horizontal", "vertical"]}
    }

    def execute(self, context, parameters):
        win_ids = parameters.get('window_ids')
        layout = parameters.get('layout')
        if not win_ids or not layout:
            return ActionResult(success=False, error="Missing parameters", error_code="MISSING_PARAM")
        try:
            results = context.services.window.arrangement.arrange(win_ids, layout)
            return ActionResult(success=True, data={"arranged": True, "windows": results})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class TileWindows(Action):
    name = "tile_windows"
    description = "Automatically tile the specified windows to fill the screen"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_ids": {"type": "list", "required": True, "description": "List of window IDs to tile"}
    }

    def execute(self, context, parameters):
        win_ids = parameters.get('window_ids')
        try:
            context.services.window.arrangement.tile(win_ids)
            return ActionResult(success=True, data={"arranged": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class CascadeWindows(Action):
    name = "cascade_windows"
    description = "Arrange windows in an overlapping cascade"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_ids": {"type": "list", "required": True}
    }

    def execute(self, context, parameters):
        win_ids = parameters.get('window_ids')
        try:
            context.services.window.arrangement.cascade(win_ids)
            return ActionResult(success=True, data={"arranged": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class StackWindows(Action):
    name = "stack_windows"
    description = "Place windows one on top of another (centered)"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_ids": {"type": "list", "required": True}
    }

    def execute(self, context, parameters):
        win_ids = parameters.get('window_ids')
        try:
            context.services.window.arrangement.stack(win_ids)
            return ActionResult(success=True, data={"arranged": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ArrangeApplicationWindows(Action):
    name = "arrange_application_windows"
    description = "Find and arrange all windows of a specific application"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "application": {"type": "string", "required": True},
        "layout": {"type": "string", "required": True, "enum": ["horizontal", "vertical", "tile"]}
    }

    def execute(self, context, parameters):
        app_name = parameters.get('application')
        layout = parameters.get('layout')
        try:
            context.services.window.arrangement.arrange_app(app_name, layout)
            return ActionResult(success=True, data={"application": app_name, "layout": layout})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ArrangeWindowsGrid(Action):
    name = "arrange_windows_grid"
    description = "Arrange windows into a specific grid of rows and columns"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_ids": {"type": "list", "required": True},
        "rows": {"type": "integer", "required": True},
        "columns": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        win_ids = parameters.get('window_ids')
        rows = parameters.get('rows')
        cols = parameters.get('columns')
        if not all([win_ids, rows, cols]):
             return ActionResult(success=False, error="Missing grid parameters")
        try:
            context.services.window.arrangement.grid(win_ids, rows, cols)
            return ActionResult(success=True, data={"arranged": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class EqualizeWindowSizes(Action):
    name = "equalize_window_sizes"
    description = "Make all specified windows the same size based on the first window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_ids": {"type": "list", "required": True}
    }

    def execute(self, context, parameters):
        win_ids = parameters.get('window_ids')
        try:
            context.services.window.arrangement.equalize(win_ids)
            return ActionResult(success=True, data={"equalized": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
