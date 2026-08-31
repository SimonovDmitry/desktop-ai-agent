from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetWindowDisplay(Action):
    name = "get_window_display"
    description = "Identify which display a specific window is currently located on"
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
            display_id = context.services.window.display.get_window_display(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "display_id": display_id})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MoveWindowToDisplay(Action):
    name = "move_window_to_display"
    description = "Move a specific window to a target display"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True},
        "display_id": {"type": "integer", "required": True, "description": "Target display ID"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        disp_id = parameters.get('display_id')
        try:
            context.services.window.display.move_to_display(win_id, disp_id)
            return ActionResult(success=True, data={"window_id": win_id, "display_id": disp_id})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MoveWindowToNextDisplay(Action):
    name = "move_window_to_next_display"
    description = "Move the window to the next available display in the system"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            new_display_id = context.services.window.display.move_to_next(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "display_id": new_display_id})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MoveWindowToPreviousDisplay(Action):
    name = "move_window_to_previous_display"
    description = "Move the window to the previous display in the system"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    parameters_schema = {"window_id": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            new_display_id = context.services.window.display.move_to_previous(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "display_id": new_display_id})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class CenterWindowOnDisplay(Action):
    name = "center_window_on_display"
    description = "Move the window to a specific display and center it within its work area"
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
            new_pos = context.services.window.display.center_on_display(win_id, disp_id)
            return ActionResult(success=True, data={"window_id": win_id, "display_id": disp_id, "position": new_pos})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MaximizeWindowOnDisplay(Action):
    name = "maximize_window_on_display"
    description = "Maximize the window on a specific display"
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
            bounds = context.services.window.display.maximize_on_display(win_id, disp_id)
            return ActionResult(success=True, data={"window_id": win_id, "display_id": disp_id, "bounds": bounds})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
