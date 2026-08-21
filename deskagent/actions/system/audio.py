from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.context import ActionContext
from deskagent.actions.types import RiskLevel, ActionCategory


class SetVolume(Action):
    name = "set_volume"
    description = "Set the system volume to a specific percentage"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "volume": {
            "type": "integer",
            "required": True,
            "minimum": 0,
            "maximum": 100,
            "description": "Volume level percentage (0-100)"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        volume = params.get('volume')

        if volume is None:
            return ActionResult(success=False, error="Parameter 'volume' is required", error_code="MISSING_PARAM")

        if not 0 <= volume <= 100:
            return ActionResult(success=False, error="Volume must be between 0 and 100", error_code="INVALID_RANGE")

        try:
            context.services.system.audio.set_volume(volume)
            return ActionResult(success=True, data={"volume": volume})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class IncreaseVolume(Action):
    name = "increase_volume"
    description = "Increase the system volume by a specified step"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "step": {
            "type": "integer",
            "required": False,
            "default": 10,
            "minimum": 1,
            "maximum": 50,
            "description": "Percentage to increase"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        step = params.get('step', 10)

        if step is None:
            step = 10

        if not 1 <= step <= 50:
            return ActionResult(success=False, error="Step must be between 1 and 50", error_code="INVALID_STEP")

        try:
            context.services.system.audio.increase_volume(step)
            return ActionResult(success=True, data={"increased_by": step})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class DecreaseVolume(Action):
    name = "decrease_volume"
    description = "Decrease the system volume by a specified step"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "step": {
            "type": "integer",
            "required": False,
            "default": 10,
            "minimum": 1,
            "maximum": 50,
            "description": "Percentage to decrease"
        }
    }

    def execute(self, context, parameters):
        params = parameters or {}
        step = params.get('step', 10)

        if step is None:
            step = 10

        if not 1 <= step <= 50:
            return ActionResult(success=False, error="Step must be between 1 and 50", error_code="INVALID_STEP")

        try:
            context.services.system.audio.decrease_volume(step)
            return ActionResult(success=True, data={"decreased_by": step})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class Mute(Action):
    name = "mute"
    description = "Mute the system audio"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.audio.mute()
            return ActionResult(success=True, data={"muted": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class Unmute(Action):
    name = "unmute"
    description = "Unmute the system audio"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.audio.unmute()
            return ActionResult(success=True, data={"muted": False})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetVolume(Action):
    name = "get_volume"
    description = "Get the current system volume level"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            volume = context.services.system.audio.get_volume()
            return ActionResult(success=True, data={"volume": volume})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")
