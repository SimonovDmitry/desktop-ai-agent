from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class SetDisplayBrightness(Action):
    name = "set_display_brightness"
    description = "Set the brightness level of the display"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "brightness_level": {
            "type": "integer",
            "required": True,
            "minimum": 0,
            "maximum": 100,
            "description": "Brightness percentage (0-100)"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        level = params.get('brightness_level')

        if level is None:
            return ActionResult(success=False, error="Parameter 'brightness_level' is required",
                                error_code="MISSING_PARAM")

        if not 0 <= level <= 100:
            return ActionResult(success=False, error="Brightness must be between 0 and 100", error_code="INVALID_INPUT")

        try:
            context.services.system.display.set_display_brightness(level)
            return ActionResult(success=True, data={"brightness": level})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetDisplayBrightness(Action):
    name = "get_display_brightness"
    description = "Get the current brightness level of the display"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
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
    parameters_schema = {}

    def execute(self, context, parameters):
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
    parameters_schema = {
        "display_id": {
            "type": "integer",
            "required": False,
            "default": 1,
            "description": "System ID of the display"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        display_id = params.get('display_id', 1)

        if display_id is None:
            display_id = 1

        try:
            size = context.services.system.display.get_screen_size(display_id)
            return ActionResult(success=True, data=size)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")

