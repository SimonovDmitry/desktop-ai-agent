from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class PressKey(Action):
    name = "press_key"
    description = "Press and hold a specific key"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "key": {"type": "string", "required": True, "description": "Key to press (e.g., 'shift', 'a', 'enter')"}
    }

    def execute(self, context, parameters):
        key = parameters.get('key')
        if not key:
            return ActionResult(success=False, error="Parameter 'key' is required", error_code="MISSING_PARAM")
        try:
            context.services.system.keyboard.press(key)
            return ActionResult(success=True, data={"key": key, "pressed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ReleaseKey(Action):
    name = "release_key"
    description = "Release a specifically pressed key"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "key": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        key = parameters.get('key')
        if not key:
            return ActionResult(success=False, error="Parameter 'key' is required", error_code="MISSING_PARAM")
        try:
            context.services.system.keyboard.release(key)
            return ActionResult(success=True, data={"key": key, "released": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class TapKey(Action):
    name = "tap_key"
    description = "Press and immediately release a key"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "key": {"type": "string", "required": True},
        "duration": {"type": "float", "required": False, "default": 0.05}
    }

    def execute(self, context, parameters):
        key = parameters.get('key')
        duration = parameters.get('duration', 0.05)
        if not key:
            return ActionResult(success=False, error="Parameter 'key' is required", error_code="MISSING_PARAM")
        try:
            context.services.system.keyboard.tap(key, duration)
            return ActionResult(success=True, data={"key": key, "pressed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class HoldKey(Action):
    name = "hold_key"
    description = "Hold a key for a specified duration"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "key": {"type": "string", "required": True},
        "duration": {"type": "float", "required": True, "description": "Seconds to hold"}
    }

    def execute(self, context, parameters):
        key = parameters.get('key')
        duration = parameters.get('duration')
        if not key or duration is None:
            return ActionResult(success=False, error="Key and duration are required", error_code="MISSING_PARAM")
        try:
            context.services.system.keyboard.hold(key, duration)
            return ActionResult(success=True, data={"key": key, "duration": duration, "completed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class ReleaseAllKeys(Action):
    name = "release_all_keys"
    description = "Emergency reset: release all logically pressed keys"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.keyboard.release_all()
            return ActionResult(success=True, data={"released": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class PressKeys(Action):
    name = "press_keys"
    description = "Press multiple keys in sequence"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "keys": {"type": "list", "required": True, "description": "List of key strings"}
    }

    def execute(self, context, parameters):
        keys = parameters.get('keys')
        if not isinstance(keys, list):
            return ActionResult(success=False, error="Keys must be a list", error_code="INVALID_INPUT")
        try:
            context.services.system.keyboard.press_sequence(keys)
            return ActionResult(success=True, data={"keys": keys, "count": len(keys)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class TypeText(Action):
    name = "type_text"
    description = "Type a string of text into the active application"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "text": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        text = parameters.get('text')
        if text is None:
            return ActionResult(success=False, error="Parameter 'text' is required", error_code="MISSING_PARAM")
        try:
            context.services.system.keyboard.type(text)
            return ActionResult(success=True, data={"text_length": len(text), "typed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class TypeTextSlowly(Action):
    name = "type_text_slowly"
    description = "Type text with a delay between characters"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "text": {"type": "string", "required": True},
        "interval": {"type": "float", "required": False, "default": 0.05}
    }

    def execute(self, context, parameters):
        text = parameters.get('text')
        interval = parameters.get('interval', 0.05)
        if text is None: return ActionResult(success=False, error="Missing text")
        try:
            context.services.system.keyboard.type(text, interval=interval)
            return ActionResult(success=True, data={"text_length": len(text), "interval": interval, "typed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class PasteText(Action):
    name = "paste_text"
    description = "Paste text using clipboard (better for long or special character strings)"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "text": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        text = parameters.get('text')
        if text is None: return ActionResult(success=False, error="Missing text")
        try:
            context.services.system.clipboard.set_clipboard(text)
            context.services.system.keyboard.paste()
            return ActionResult(success=True, data={"text_length": len(text), "pasted": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class CopySelection(Action):
    name = "copy_selection"
    description = "Copy current selection to clipboard"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.keyboard.copy()
            return ActionResult(success=True, data={"copied": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class CutSelection(Action):
    name = "cut_selection"
    description = "Cut current selection to clipboard"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.keyboard.cut()
            return ActionResult(success=True, data={"cut": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class SelectAll(Action):
    name = "select_all"
    description = "Select all content in the active field/window"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.keyboard.select_all()
            return ActionResult(success=True, data={"selected": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class DeleteSelection(Action):
    name = "delete_selection"
    description = "Delete currently selected content"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.keyboard.delete()
            return ActionResult(success=True, data={"deleted": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetKeyboardState(Action):
    name = "get_keyboard_state"
    description = "Get list of currently pressed modifier keys"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            state = context.services.system.keyboard.get_state()
            return ActionResult(success=True, data=state)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))