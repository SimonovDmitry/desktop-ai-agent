from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory
import time


class MoveAndClick(Action):
    name = "move_and_click"
    description = "Moves the mouse to coordinates and performs a single click"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "x": {"type": "integer", "required": True},
        "y": {"type": "integer", "required": True},
        "button": {"type": "string", "required": False, "default": "left", "enum": ["left", "right", "middle"]}
    }

    def execute(self, context, parameters):
        x, y = parameters.get('x'), parameters.get('y')
        btn = parameters.get('button', 'left')
        if x is None or y is None:
            return ActionResult(success=False, error="X and Y coordinates are required", error_code="MISSING_PARAM")

        try:
            context.services.system.mouse.move_mouse(x, y)
            time.sleep(0.05)
            context.services.system.mouse.click(btn)
            return ActionResult(success=True, data={"position": {"x": x, "y": y}, "button": btn, "clicked": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class MoveAndDoubleClick(Action):
    name = "move_and_double_click"
    description = "Moves the mouse to coordinates and performs a double click"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "x": {"type": "integer", "required": True},
        "y": {"type": "integer", "required": True},
        "button": {"type": "string", "required": False, "default": "left"}
    }

    def execute(self, context, parameters):
        x, y = parameters.get('x'), parameters.get('y')
        btn = parameters.get('button', 'left')
        try:
            context.services.system.mouse.move_mouse(x, y)
            time.sleep(0.05)
            context.services.system.mouse.double_click(btn)
            return ActionResult(success=True,
                                data={"position": {"x": x, "y": y}, "button": btn, "clicked": True, "click_count": 2})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class DragGesture(Action):
    name = "drag_gesture"
    description = "Performs a complete drag-and-drop operation from start to end coordinates"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "start_x": {"type": "integer", "required": True},
        "start_y": {"type": "integer", "required": True},
        "end_x": {"type": "integer", "required": True},
        "end_y": {"type": "integer", "required": True},
        "button": {"type": "string", "required": False, "default": "left"},
        "duration": {"type": "float", "required": False, "default": 0.5}
    }

    def execute(self, context, parameters):
        p = parameters
        try:
            context.services.system.mouse.drag_mouse(
                p['start_x'], p['start_y'],
                p['end_x'], p['end_y'],
                p.get('button', 'left'),
                p.get('duration', 0.5)
            )
            return ActionResult(success=True, data={"gesture": "drag", "completed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SwipeGesture(Action):
    name = "swipe_gesture"
    description = "Simulates a quick smooth swipe motion between two points"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "start_x": {"type": "integer", "required": True},
        "start_y": {"type": "integer", "required": True},
        "end_x": {"type": "integer", "required": True},
        "end_y": {"type": "integer", "required": True},
        "duration": {"type": "float", "required": False, "default": 0.3}
    }

    def execute(self, context, parameters):
        p = parameters
        try:
            context.services.system.mouse.move_smooth(p['start_x'], p['start_y'], 0.05)
            context.services.system.mouse.move_smooth(p['end_x'], p['end_y'], p.get('duration', 0.3))
            return ActionResult(success=True, data={"gesture": "swipe", "completed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ClickAndHold(Action):
    name = "click_and_hold"
    description = "Presses a mouse button and holds it for a specific duration"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "button": {"type": "string", "required": False, "default": "left"},
        "duration": {"type": "float", "required": True, "description": "Seconds to hold"}
    }

    def execute(self, context, parameters):
        btn = parameters.get('button', 'left')
        dur = parameters.get('duration')
        try:
            context.services.system.mouse.mouse_down(btn)
            time.sleep(dur)
            context.services.system.mouse.mouse_up(btn)
            return ActionResult(success=True, data={"button": btn, "duration": dur, "completed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ScrollGesture(Action):
    name = "scroll_gesture"
    description = "Simplified scrolling using directions"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "direction": {"type": "string", "required": True, "enum": ["up", "down", "left", "right"]},
        "amount": {"type": "integer", "required": True, "description": "Magnitude of scroll"}
    }

    def execute(self, context, parameters):
        direction = parameters.get('direction')
        amount = parameters.get('amount')
        try:
            if direction == "up":
                context.services.system.mouse.scroll_mouse(amount)
            elif direction == "down":
                context.services.system.mouse.scroll_mouse(-amount)
            elif direction == "left":
                context.services.system.mouse.scroll_horizontal(-amount)
            elif direction == "right":
                context.services.system.mouse.scroll_horizontal(amount)

            return ActionResult(success=True, data={"direction": direction, "amount": amount, "completed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class MultiClickGesture(Action):
    name = "multi_click_gesture"
    description = "Performs a specified number of clicks in rapid succession"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "count": {"type": "integer", "required": True},
        "button": {"type": "string", "required": False, "default": "left"},
        "interval": {"type": "float", "required": False, "default": 0.1}
    }

    def execute(self, context, parameters):
        count = parameters.get('count')
        btn = parameters.get('button', 'left')
        interval = parameters.get('interval', 0.1)
        try:
            for _ in range(count):
                context.services.system.mouse.click(btn)
                time.sleep(interval)
            return ActionResult(success=True, data={"count": count, "completed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))