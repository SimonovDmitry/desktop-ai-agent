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

    def execute(self, context):
        try:
            position = context.services.system.mouse.get_cursor_position()
            return ActionResult(success=True, data=position)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать метод перемещения в платформенном сервисе
class MoveMouse(Action):
    name = "move_mouse"
    description = "Move the mouse cursor to specific coordinates"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True

    def execute(self, context, x, y):
        try:
            context.services.system.mouse.move_mouse(x, y)
            return ActionResult(success=True, data={"x": x, "y": y})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать метод клика в платформенном сервисе
class Click(Action):
    name = "click"
    description = "Perform a mouse click at the current or specified position"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    reversible = True

    def execute(self, context, button='left'):
        try:
            context.services.system.mouse.click(button)
            return ActionResult(success=True, data={"button": button})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать метод двойного клика в платформенном сервисе
class DoubleClick(Action):
    name = "double_click"
    description = "Perform a double mouse click"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    reversible = True

    def execute(self, context, button='left'):
        try:
            context.services.system.mouse.double_click(button)
            return ActionResult(success=True, data={"button": button})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать метод перетаскивания в платформенном сервисе
class DragMouse(Action):
    name = "drag_mouse"
    description = "Drag the mouse from one point to another"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = False
    reversible = True

    def execute(self, context, x1, y1, x2, y2):
        try:
            context.services.system.mouse.drag_mouse(x1, y1, x2, y2)
            return ActionResult(success=True, data={"from": (x1, y1), "to": (x2, y2)})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать метод прокрутки в платформенном сервисе
class ScrollMouse(Action):
    name = "scroll_mouse"
    description = "Scroll the mouse wheel"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True

    def execute(self, context, clicks):
        try:
            context.services.system.mouse.scroll_mouse(clicks)
            return ActionResult(success=True, data={"clicks": clicks})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
