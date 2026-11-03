from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


def _get_mouse(context):
    if hasattr(context.services, "system") and hasattr(context.services.system, "mouse"):
        return context.services.system.mouse
    if hasattr(context.services, "input") and hasattr(context.services.input, "mouse"):
        return context.services.input.mouse
    return getattr(context.services, "mouse", None)


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
            m = _get_mouse(context)
            if hasattr(m, "get_cursor_position"):
                pos = m.get_cursor_position()
            else:
                pos = m.get_mouse_position()
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
            m = _get_mouse(context)
            if hasattr(m, "get_button_state"):
                state = m.get_button_state()
            else:
                state = m.get_mouse_button_state()
            return ActionResult(success=True, data=state)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class MoveMouse(Action):
    name = "move_mouse"
    description = "Move the mouse cursor to absolute screen coordinates"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {"x": {"type": "integer", "required": True}, "y": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        p = parameters or {}
        x, y = p.get("x"), p.get("y")
        if x is None or y is None:
            return ActionResult(success=False, error="X and Y are required", error_code="MISSING_PARAM")
        try:
            _get_mouse(context).move_mouse(x, y)
            return ActionResult(success=True, data={"x": x, "y": y, "moved": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class MoveMouseRelative(Action):
    name = "move_mouse_relative"
    description = "Move the mouse cursor relative to its current position"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "dx": {"type": "integer", "required": True, "description": "Horizontal offset"},
        "dy": {"type": "integer", "required": True, "description": "Vertical offset"},
    }

    def execute(self, context, parameters):
        p = parameters or {}
        dx, dy = p.get("dx"), p.get("dy")
        try:
            m = _get_mouse(context)
            if hasattr(m, "move_relative"):
                new_pos = m.move_relative(dx, dy)
            else:
                new_pos = m.move_mouse_relative(dx, dy)
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
        "duration": {"type": "float", "required": False, "default": 0.5},
    }

    def execute(self, context, parameters):
        p = parameters or {}
        x, y = p.get("x"), p.get("y")
        duration = p.get("duration", 0.5)
        try:
            m = _get_mouse(context)
            if hasattr(m, "move_smooth"):
                m.move_smooth(x, y, duration)
            else:
                m.move_mouse_smoothly(x, y, duration)
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
        p = parameters or {}
        btn = p.get("button", "left")
        try:
            m = _get_mouse(context)
            if hasattr(m, "click"):
                m.click(btn)
            else:
                m.click_mouse(btn)
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
        p = parameters or {}
        btn = p.get("button", "left")
        try:
            m = _get_mouse(context)
            if hasattr(m, "double_click"):
                m.double_click(btn)
            else:
                m.double_click_mouse(btn)
            return ActionResult(success=True, data={"button": btn, "clicked": True, "click_count": 2})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class TripleClickMouse(Action):
    name = "triple_click_mouse"
    description = "Perform a triple mouse click (useful for selecting paragraphs)"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {"button": {"type": "string", "required": False, "default": "left"}}

    def execute(self, context, parameters):
        p = parameters or {}
        btn = p.get("button", "left")
        try:
            m = _get_mouse(context)
            if hasattr(m, "triple_click"):
                m.triple_click(btn)
            else:
                m.triple_click_mouse(btn)
            return ActionResult(success=True, data={"button": btn, "click_count": 3})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class MouseDown(Action):
    name = "mouse_down"
    description = "Press and hold a mouse button"
    category = ActionCategory.SYSTEM
    reversible = True
    parameters_schema = {"button": {"type": "string", "required": True, "enum": ["left", "right", "middle"]}}

    def execute(self, context, parameters):
        p = parameters or {}
        btn = p.get("button", "left")
        try:
            _get_mouse(context).mouse_down(btn)
            return ActionResult(success=True, data={"button": btn, "pressed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class MouseUp(Action):
    name = "mouse_up"
    description = "Release a pressed mouse button"
    category = ActionCategory.SYSTEM
    parameters_schema = {"button": {"type": "string", "required": True, "enum": ["left", "right", "middle"]}}

    def execute(self, context, parameters):
        p = parameters or {}
        btn = p.get("button", "left")
        try:
            _get_mouse(context).mouse_up(btn)
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
        "duration": {"type": "float", "required": False, "default": 0.5},
    }

    def execute(self, context, parameters):
        p = parameters or {}
        for key in ("x1", "y1", "x2", "y2"):
            if key not in p or p.get(key) is None:
                return ActionResult(success=False, error=f"Parameter '{key}' is required", error_code="MISSING_PARAM")

        x1, y1, x2, y2 = p["x1"], p["y1"], p["x2"], p["y2"]
        try:
            m = _get_mouse(context)
            if "button" in p:
                m.drag_mouse(x1, y1, x2, y2, p["button"])
            else:
                m.drag_mouse(x1, y1, x2, y2)
            return ActionResult(
                success=True,
                data={"from": {"x": x1, "y": y1}, "to": {"x": x2, "y": y2}},
            )
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class DragMouseRelative(Action):
    name = "drag_mouse_relative"
    description = "Drag from the current cursor position by a relative offset"
    category = ActionCategory.INPUT
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "dx": {"type": "integer", "required": True},
        "dy": {"type": "integer", "required": True},
        "button": {"type": "string", "required": False, "default": "left"},
        "duration": {"type": "float", "required": False, "default": 0.5},
    }

    def execute(self, context, parameters):
        p = parameters or {}
        try:
            _get_mouse(context).drag_mouse_relative(
                p["dx"], p["dy"], p.get("button", "left"), p.get("duration", 0.5)
            )
            return ActionResult(success=True, data={"dragged": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ScrollMouse(Action):
    name = "scroll_mouse"
    description = "Vertical scroll (positive for up, negative for down)"
    category = ActionCategory.SYSTEM
    parameters_schema = {"clicks": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        p = parameters or {}
        if "clicks" not in p or p.get("clicks") is None:
            return ActionResult(success=False, error="Parameter 'clicks' is required", error_code="MISSING_PARAM")
        clicks = p.get("clicks")
        try:
            _get_mouse(context).scroll_mouse(clicks)
            return ActionResult(success=True, data={"clicks": clicks, "scrolled": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class HorizontalScrollMouse(Action):
    name = "horizontal_scroll_mouse"
    description = "Horizontal scroll"
    category = ActionCategory.SYSTEM
    parameters_schema = {"clicks": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        p = parameters or {}
        if "clicks" not in p or p.get("clicks") is None:
            return ActionResult(success=False, error="Parameter 'clicks' is required", error_code="MISSING_PARAM")
        clicks = p.get("clicks")
        try:
            m = _get_mouse(context)
            if hasattr(m, "scroll_horizontal"):
                m.scroll_horizontal(clicks)
            else:
                m.horizontal_scroll_mouse(clicks)
            return ActionResult(success=True, data={"clicks": clicks, "scrolled": True, "direction": "horizontal"})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))
