from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.context import ActionContext
from deskagent.actions.types import RiskLevel, ActionCategory


class SetDisplayBrightness(Action):
    name = "set_display_brightness"
    description = "Set the brightness level of the display"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True

    def execute(self, context, brightness_level):
        if not 0 <= brightness_level <= 100:
            return ActionResult(success=False, error="Brightness must be between 0 and 100", error_code="INVALID_INPUT")

        try:
            context.services.system.display.set_display_brightness(brightness_level)
            return ActionResult(success=True, data={"brightness": brightness_level})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetDisplayBrightness(Action):
    name = "get_display_brightness"
    description = "Get the current brightness level of the display"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            brightness = context.services.system.display.get_display_brightness()
            if brightness is None:
                return ActionResult(success=False, error="Could not retrieve brightness level",
                                    error_code="NOT_SUPPORTED")

            return ActionResult(success=True, data={"brightness": brightness})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetDisplays(Action):
    name = "get_displays"
    description = "Get information about all connected displays"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            displays = context.services.system.display.get_displays()
            return ActionResult(success=True, data={"displays": displays, "count": len(displays)})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetScreenSize(Action):
    name = "get_screen_size"
    description = "Get the logical size of a specific display or the primary screen"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context, display_id=1):
        try:
            size = context.services.system.display.get_screen_size(display_id)
            return ActionResult(success=True, data=size)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class SetResolution(Action):
    name = "set_resolution"
    description = "Change the screen resolution for a specific display"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM  # Смена разрешения может быть деструктивной для UI
    requires_confirmation = True
    reversible = True

    def execute(self, context, display_id, width, height):
        try:
            context.services.system.display.set_resolution(display_id, width, height)
            return ActionResult(success=True, data={"display_id": display_id, "width": width, "height": height})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")