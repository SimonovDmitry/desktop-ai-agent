from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetWindowState(Action):
    name = "get_window_state"
    description = "Get the current visual state of a specific window (normal, minimized, maximized, etc.)"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            state = context.services.window.state.get_state(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "state": state})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SetWindowState(Action):
    name = "set_window_state"
    description = "Set a specific visual state for a window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True},
        "state": {
            "type": "string",
            "required": True,
            "enum": ["normal", "minimized", "maximized", "fullscreen", "hidden"],
            "description": "Target state for the window"
        }
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        state = parameters.get('state')
        try:
            context.services.window.state.set_state(win_id, state)
            return ActionResult(success=True, data={"window_id": win_id, "state": state})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MinimizeWindow(Action):
    name = "minimize_window"
    description = "Minimize a specific window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.state.minimize(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "state": "minimized"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MaximizeWindow(Action):
    name = "maximize_window"
    description = "Maximize a specific window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.state.maximize(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "state": "maximized"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class RestoreWindow(Action):
    name = "restore_window"
    description = "Restore a window to its normal (unmaximized/unminimized) state"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.state.restore(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "state": "normal"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class HideWindow(Action):
    name = "hide_window"
    description = "Hide a specific window from the screen"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.state.hide(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "hidden": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ShowWindow(Action):
    name = "show_window"
    description = "Make a hidden window visible again"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.state.show(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "visible": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ToggleWindowVisibility(Action):
    name = "toggle_window_visibility"
    description = "Switch the window between visible and hidden states"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            new_visibility = context.services.window.state.toggle_visibility(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "visible": new_visibility})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ToggleWindowState(Action):
    name = "toggle_window_state"
    description = "Toggle between normal and maximized window states"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            new_state = context.services.window.state.toggle_state(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "state": new_state})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
