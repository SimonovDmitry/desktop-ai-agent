from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class SetWindowAlwaysOnTop(Action):
    name = "set_window_always_on_top"
    description = "Keep a specific window on top of all other windows"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"},
        "enabled": {"type": "boolean", "required": True, "description": "True to enable, False to disable"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        enabled = parameters.get('enabled')
        try:
            context.services.window.appearance.set_always_on_top(win_id, enabled)
            return ActionResult(success=True, data={"window_id": win_id, "always_on_top": enabled})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class RemoveWindowAlwaysOnTop(Action):
    name = "remove_window_always_on_top"
    description = "Disable the 'always on top' state for a specific window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.appearance.set_always_on_top(win_id, False)
            return ActionResult(success=True, data={"window_id": win_id, "always_on_top": False})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetWindowAlwaysOnTop(Action):
    name = "get_window_always_on_top"
    description = "Check if a specific window is currently in 'always on top' mode"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            is_on_top = context.services.window.appearance.is_always_on_top(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "always_on_top": is_on_top})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SetWindowOpacity(Action):
    name = "set_window_opacity"
    description = "Set the transparency level of a specific window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True},
        "opacity": {
            "type": "float",
            "required": True,
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Opacity value from 0.0 (transparent) to 1.0 (opaque)"
        }
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        opacity = parameters.get('opacity')
        try:
            context.services.window.appearance.set_opacity(win_id, opacity)
            return ActionResult(success=True, data={"window_id": win_id, "opacity": opacity})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetWindowOpacity(Action):
    name = "get_window_opacity"
    description = "Get the current opacity level of a window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            opacity = context.services.window.appearance.get_opacity(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "opacity": opacity})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SetWindowFullscreen(Action):
    name = "set_window_fullscreen"
    description = "Enter fullscreen mode for a specific window"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.appearance.set_fullscreen(win_id, True)
            return ActionResult(success=True, data={"window_id": win_id, "fullscreen": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ExitWindowFullscreen(Action):
    name = "exit_window_fullscreen"
    description = "Exit fullscreen mode and return window to normal state"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            context.services.window.appearance.set_fullscreen(win_id, False)
            return ActionResult(success=True, data={"window_id": win_id, "fullscreen": False})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ToggleWindowFullscreen(Action):
    name = "toggle_window_fullscreen"
    description = "Switch a window between fullscreen and normal mode"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            new_state = context.services.window.appearance.toggle_fullscreen(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "fullscreen": new_state})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
