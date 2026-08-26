from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class MoveWindow(Action):
    name = "move_window"
    description = "Move a specific window relative to its current position"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window to move"},
        "dx": {"type": "integer", "required": True, "description": "Delta X (horizontal shift)"},
        "dy": {"type": "integer", "required": True, "description": "Delta Y (vertical shift)"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        dx = parameters.get('dx')
        dy = parameters.get('dy')
        try:
            new_pos = context.services.window.position.move(win_id, dx, dy)
            return ActionResult(success=True, data={"window_id": win_id, "position": new_pos})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MoveWindowTo(Action):
    name = "move_window_to"
    description = "Move a specific window to absolute coordinates"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window to move"},
        "x": {"type": "integer", "required": True, "description": "Target X coordinate"},
        "y": {"type": "integer", "required": True, "description": "Target Y coordinate"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        x = parameters.get('x')
        y = parameters.get('y')
        try:
            context.services.window.position.move_to(win_id, x, y)
            return ActionResult(success=True, data={"window_id": win_id, "position": {"x": x, "y": y}})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class CenterWindow(Action):
    name = "center_window"
    description = "Center the window on its current display"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window to center"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            new_pos = context.services.window.position.center(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "position": new_pos})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class CenterWindowOnDisplay(Action):
    name = "center_window_on_display"
    description = "Move the window to a specific display and center it"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"},
        "display_id": {"type": "integer", "required": True, "description": "Target display ID"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        disp_id = parameters.get('display_id')
        try:
            new_pos = context.services.window.position.center_on_display(win_id, disp_id)
            return ActionResult(success=True, data={"window_id": win_id, "display_id": disp_id, "position": new_pos})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MoveWindowToDisplay(Action):
    name = "move_window_to_display"
    description = "Move the window to a specific display while maintaining relative position"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"},
        "display_id": {"type": "integer", "required": True, "description": "Target display ID"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        disp_id = parameters.get('display_id')
        try:
            context.services.window.position.move_to_display(win_id, disp_id)
            return ActionResult(success=True, data={"window_id": win_id, "display_id": disp_id})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SnapWindowLeft(Action):
    name = "snap_window_left"
    description = "Position the window to fill the left half of the display"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            result = context.services.window.position.snap(win_id, "left")
            return ActionResult(success=True, data={"window_id": win_id, "position": result['pos'], "size": result['size']})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SnapWindowRight(Action):
    name = "snap_window_right"
    description = "Position the window to fill the right half of the display"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            result = context.services.window.position.snap(win_id, "right")
            return ActionResult(success=True, data={"window_id": win_id, "position": result['pos'], "size": result['size']})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SnapWindowTop(Action):
    name = "snap_window_top"
    description = "Position the window to fill the top half of the display"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            result = context.services.window.position.snap(win_id, "top")
            return ActionResult(success=True, data={"window_id": win_id, "position": result['pos'], "size": result['size']})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SnapWindowBottom(Action):
    name = "snap_window_bottom"
    description = "Position the window to fill the bottom half of the display"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            result = context.services.window.position.snap(win_id, "bottom")
            return ActionResult(success=True, data={"window_id": win_id, "position": result['pos'], "size": result['size']})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class RestoreWindowPosition(Action):
    name = "restore_window_position"
    description = "Restore the window to its previous position and size"
    category = ActionCategory.APPLICATION
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "window_id": {"type": "integer", "required": True, "description": "ID of the window to restore"}
    }

    def execute(self, context, parameters):
        win_id = parameters.get('window_id')
        try:
            old_pos = context.services.window.position.restore_position(win_id)
            return ActionResult(success=True, data={"window_id": win_id, "position": old_pos})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
