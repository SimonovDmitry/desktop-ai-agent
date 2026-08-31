from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class ResizeWindow(Action):
    name = "resize_window"
    description = "Change the window size relative to its current dimensions"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"},
        "delta_width": {"type": "integer", "required": True, "description": "Value to add to current width"},
        "delta_height": {"type": "integer", "required": True, "description": "Value to add to current height"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        dw = parameters.get('delta_width')
        dh = parameters.get('delta_height')
        try:
            new_size = context.services.window.size.resize_relative(win_id, dw, dh)
            return ActionResult(success=True, data={"window_id": win_id, "width": new_size['width'], "height": new_size['height']})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ResizeWindowTo(Action):
    name = "resize_window_to"
    description = "Set the window size to specific absolute dimensions"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True},
        "width": {"type": "integer", "required": True},
        "height": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        w = parameters.get('width')
        h = parameters.get('height')
        try:
            context.services.window.size.resize_absolute(win_id, w, h)
            return ActionResult(success=True, data={"window_id": win_id, "size": {"width": w, "height": h}})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SetWindowWidth(Action):
    name = "set_window_width"
    description = "Change only the width of a specific window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_id": {"type": "integer", "required": True},
        "width": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        w = parameters.get('width')
        try:
            context.services.window.size.set_width(win_id, w)
            return ActionResult(success=True, data={"width": w})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SetWindowHeight(Action):
    name = "set_window_height"
    description = "Change only the height of a specific window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_id": {"type": "integer", "required": True},
        "height": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        h = parameters.get('height')
        try:
            context.services.window.size.set_height(win_id, h)
            return ActionResult(success=True, data={"height": h})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SetWindowSize(Action):
    name = "set_window_size"
    description = "Set both width and height of a window (Alias for resize_window_to)"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_id": {"type": "integer", "required": True},
        "width": {"type": "integer", "required": True},
        "height": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        w = parameters.get('width')
        h = parameters.get('height')
        try:
            context.services.window.size.resize_absolute(win_id, w, h)
            return ActionResult(success=True, data={"width": w, "height": h})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class FitWindowToDisplay(Action):
    name = "fit_window_to_display"
    description = "Adjust the window to fit the work area of a specific display"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_id": {"type": "integer", "required": True},
        "display_id": {"type": "integer", "required": True, "description": "ID of the target display"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        disp_id = parameters.get('display_id')
        try:
            bounds = context.services.window.size.fit_to_display(win_id, disp_id)
            return ActionResult(success=True, data={"window_id": win_id, "bounds": bounds})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MaximizeWindowToDisplay(Action):
    name = "maximize_window_to_display"
    description = "Maximize the window on the work area of a specific display"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "window_id": {"type": "integer", "required": True},
        "display_id": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        disp_id = parameters.get('display_id')
        try:
            bounds = context.services.window.size.maximize_on_display(win_id, disp_id)
            return ActionResult(success=True, data={"window_id": win_id, "bounds": bounds})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class RestoreWindowSize(Action):
    name = "restore_window_size"
    description = "Revert the window to its previous size before the last resize operation"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    reversible = False
    parameters_schema = {
        "window_id": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            old_size = context.services.window.size.restore_size(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "size": old_size})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
