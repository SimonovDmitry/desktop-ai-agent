from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.context import ActionContext
from deskagent.actions.types import RiskLevel, ActionCategory


class GetCursorPosition(Action):
    name = "get_cursor_position"
    description = "Get the current X and Y coordinates of the mouse cursor"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            position = context.services.system.mouse.get_cursor_position()
            return ActionResult(success=True, data=position)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MoveMouse(Action):
    name = "move_mouse"
    description = "Move the mouse cursor to specific coordinates"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "x": {"type": "integer", "required": True, "description": "Target X coordinate"},
        "y": {"type": "integer", "required": True, "description": "Target Y coordinate"}
    }

    def execute(self, context, parameters):
        params = parameters or {}
        x = params.get('x')
        y = params.get('y')

        if x is None or y is None:
            return ActionResult(success=False, error="Parameters 'x' and 'y' are required", error_code="MISSING_PARAM")

        try:
            context.services.system.mouse.move_mouse(x, y)
            return ActionResult(success=True, data={"x": x, "y": y})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class Click(Action):
    name = "click"
    description = "Perform a mouse click at the current position"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "button": {
            "type": "string",
            "required": False,
            "default": "left",
            "enum": ["left", "right", "middle"],
            "description": "Mouse button to click"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        button = params.get('button', 'left')

        if button is None:
            button = 'left'

        try:
            context.services.system.mouse.click(button)
            return ActionResult(success=True, data={"button": button})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class DoubleClick(Action):
    name = "double_click"
    description = "Perform a double mouse click"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "button": {
            "type": "string",
            "required": False,
            "default": "left",
            "enum": ["left", "right", "middle"]
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        button = params.get('button', 'left')

        if button is None:
            button = 'left'

        try:
            context.services.system.mouse.double_click(button)
            return ActionResult(success=True, data={"button": button})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class DragMouse(Action):
    name = "drag_mouse"
    description = "Drag the mouse from one point to another"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "x1": {"type": "integer", "required": True},
        "y1": {"type": "integer", "required": True},
        "x2": {"type": "integer", "required": True},
        "y2": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        params = parameters or {}
        x1, y1 = params.get('x1'), params.get('y1')
        x2, y2 = params.get('x2'), params.get('y2')

        if any(v is None for v in (x1, y1, x2, y2)):
            return ActionResult(success=False, error="Parameters 'x1', 'y1', 'x2', and 'y2' are required",
                                error_code="MISSING_PARAM")

        try:
            context.services.system.mouse.drag_mouse(x1, y1, x2, y2)
            return ActionResult(success=True, data={"from": (x1, y1), "to": (x2, y2)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ScrollMouse(Action):
    name = "scroll_mouse"
    description = "Scroll the mouse wheel"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "clicks": {"type": "integer", "required": True,
                   "description": "Number of clicks to scroll (positive for up, negative for down)"}
    }

    def execute(self, context, parameters):
        params = parameters or {}
        clicks = params.get('clicks')

        if clicks is None:
            return ActionResult(success=False, error="Parameter 'clicks' is required", error_code="MISSING_PARAM")

        try:
            context.services.system.mouse.scroll_mouse(clicks)
            return ActionResult(success=True, data={"clicks": clicks})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
