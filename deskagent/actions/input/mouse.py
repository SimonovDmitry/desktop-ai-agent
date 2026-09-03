from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetMousePosition(Action):
    name = "get_mouse_position"
    description = "Get the current X and Y coordinates of the mouse cursor"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            pos = context.services.system.mouse.get_cursor_position()
            return ActionResult(success=True, data=pos)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetMouseButtonState(Action):
    name = "get_mouse_button_state"
    description = "Check if mouse buttons (left, right, middle) are currently pressed"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            state = context.services.system.mouse.get_button_state()
            return ActionResult(success=True, data=state)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class MoveMouse(Action):
    name = "move_mouse"
    description = "Move the mouse cursor to absolute screen coordinates"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "x": {"type": "integer", "required": True},
        "y": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        x, y = parameters.get('x'), parameters.get('y')
        if x is None or y is None:
            return ActionResult(success=False, error="X and Y are required", error_code="MISSING_PARAM")
        try:
            context.services.system.mouse.move_mouse(x, y)
            return ActionResult(success=True, data={"x": x, "y": y, "moved": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class MoveMouseRelative(Action):
    name = "move_mouse_relative"
    description = "Move the mouse cursor relative to its current position"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "dx": {"type": "integer", "required": True, "description": "Horizontal offset"},
        "dy": {"type": "integer", "required": True, "description": "Vertical offset"}
    }

    def execute(self, context, parameters):
        dx, dy = parameters.get('dx'), parameters.get('dy')
        try:
            new_pos = context.services.system.mouse.move_relative(dx, dy)
            return ActionResult(success=True, data={"dx": dx, "dy": dy, "moved": True, "new_pos": new_pos})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class MoveMouseSmoothly(Action):
    name = "move_mouse_smoothly"
    description = "Move the mouse cursor to coordinates with a visible glide animation"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "x": {"type": "integer", "required": True},
        "y": {"type": "integer", "required": True},
        "duration": {"type": "float", "required": False, "default": 0.5}
    }

    def execute(self, context, parameters):
        x, y = parameters.get('x'), parameters.get('y')
        duration = parameters.get('duration', 0.5)
        try:
            context.services.system.mouse.move_smooth(x, y, duration)
            return ActionResult(success=True, data={"x": x, "y": y, "duration": duration, "moved": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ClickMouse(Action):
    name = "click_mouse"
    description = "Perform a single mouse click"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "button": {"type": "string", "required": False, "default": "left", "enum": ["left", "right", "middle"]}
    }

    def execute(self, context, parameters):
        btn = parameters.get('button', 'left')
        try:
            context.services.system.mouse.click(btn)
            return ActionResult(success=True, data={"button": btn, "clicked": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class DoubleClickMouse(Action):
    name = "double_click_mouse"
    description = "Perform a double mouse click"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "button": {"type": "string", "required": False, "default": "left", "enum": ["left", "right", "middle"]}
    }

    def execute(self, context, parameters):
        btn = parameters.get('button', 'left')
        try:
            context.services.system.mouse.double_click(btn)
            return ActionResult(success=True, data={"button": btn, "clicked": True, "click_count": 2})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class TripleClickMouse(Action):
    name = "triple_click_mouse"
    description = "Perform a triple mouse click (useful for selecting paragraphs)"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "button": {"type": "string", "required": False, "default": "left"}
    }

    def execute(self, context, parameters):
        btn = parameters.get('button', 'left')
        try:
            context.services.system.mouse.triple_click(btn)
            return ActionResult(success=True, data={"button": btn, "click_count": 3})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class MouseDown(Action):
    name = "mouse_down"
    description = "Press and hold a mouse button"
    category = ActionCategory.SYSTEM
    reversible = True
    parameters_schema = {
        "button": {"type": "string", "required": True, "enum": ["left", "right", "middle"]}
    }

    def execute(self, context, parameters):
        btn = parameters.get('button')
        try:
            context.services.system.mouse.mouse_down(btn)
            return ActionResult(success=True, data={"button": btn, "pressed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class MouseUp(Action):
    name = "mouse_up"
    description = "Release a pressed mouse button"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "button": {"type": "string", "required": True, "enum": ["left", "right", "middle"]}
    }

    def execute(self, context, parameters):
        btn = parameters.get('button')
        try:
            context.services.system.mouse.mouse_up(btn)
            return ActionResult(success=True, data={"button": btn, "released": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class DragMouse(Action):
    name = "drag_mouse"
    description = "Drag from one point to another"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "x1": {"type": "integer", "required": True},
        "y1": {"type": "integer", "required": True},
        "x2": {"type": "integer", "required": True},
        "y2": {"type": "integer", "required": True},
        "button": {"type": "string", "required": False, "default": "left"},
        "duration": {"type": "float", "required": False, "default": 0.5}
    }

    def execute(self, context, parameters):
        p = parameters
        try:
            context.services.system.mouse.drag_mouse(p['x1'], p['y1'], p['x2'], p['y2'], p.get('button', 'left'))
            return ActionResult(success=True, data={
                "from": {"x": p['x1'], "y": p['y1']},
                "to": {"x": p['x2'], "y": p['y2']},
                "dragged": True
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ScrollMouse(Action):
    name = "scroll_mouse"
    description = "Vertical scroll (positive for up, negative for down)"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "clicks": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        clicks = parameters.get('clicks')
        try:
            context.services.system.mouse.scroll_mouse(clicks)
            return ActionResult(success=True, data={"clicks": clicks, "scrolled": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class HorizontalScrollMouse(Action):
    name = "horizontal_scroll_mouse"
    description = "Horizontal scroll"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "clicks": {"type": "integer", "required": True}
    }

    def execute(self, context, parameters):
        clicks = parameters.get('clicks')
        try:
            context.services.system.mouse.scroll_horizontal(clicks)
            return ActionResult(success=True, data={"clicks": clicks, "scrolled": True, "direction": "horizontal"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))