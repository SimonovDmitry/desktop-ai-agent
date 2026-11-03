from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


def _get_keyboard(context):
    if hasattr(context.services, "system") and hasattr(context.services.system, "keyboard"):
        return context.services.system.keyboard
    if hasattr(context.services, "input") and hasattr(context.services.input, "keyboard"):
        return context.services.input.keyboard
    return getattr(context.services, "keyboard", None)


def _get_clipboard(context):
    if hasattr(context.services, "system") and hasattr(context.services.system, "clipboard"):
        return context.services.system.clipboard
    if hasattr(context.services, "input") and hasattr(context.services.input, "clipboard"):
        return context.services.input.clipboard
    return getattr(context.services, "clipboard", None)


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
        p = parameters or {}
        key = p.get("key")
        if not key:
            return ActionResult(success=False, error="Parameter 'key' is required", error_code="MISSING_PARAM")
        try:
            kb = _get_keyboard(context)
            if hasattr(kb, "press"):
                kb.press(key)
            else:
                kb.press_key(key)
            return ActionResult(success=True, data={"key": key, "pressed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ReleaseKey(Action):
    name = "release_key"
    description = "Release a specifically pressed key"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {"key": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        p = parameters or {}
        key = p.get("key")
        if not key:
            return ActionResult(success=False, error="Parameter 'key' is required", error_code="MISSING_PARAM")
        try:
            kb = _get_keyboard(context)
            if hasattr(kb, "release"):
                kb.release(key)
            else:
                kb.release_key(key)
            return ActionResult(success=True, data={"key": key, "released": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class TapKey(Action):
    name = "tap_key"
    description = "Press and immediately release a key"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "key": {"type": "string", "required": True},
        "duration": {"type": "float", "required": False, "default": 0.05},
    }

    def execute(self, context, parameters):
        p = parameters or {}
        key = p.get("key")
        duration = p.get("duration", 0.05)
        if not key:
            return ActionResult(success=False, error="Parameter 'key' is required", error_code="MISSING_PARAM")
        try:
            kb = _get_keyboard(context)
            if hasattr(kb, "tap"):
                kb.tap(key, duration)
            else:
                kb.tap_key(key, duration)
            return ActionResult(success=True, data={"key": key, "pressed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class HoldKey(Action):
    name = "hold_key"
    description = "Hold a key for a specified duration"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {
        "key": {"type": "string", "required": True},
        "duration": {"type": "float", "required": True, "description": "Seconds to hold"},
    }

    def execute(self, context, parameters):
        p = parameters or {}
        key = p.get("key")
        duration = p.get("duration")
        if not key or duration is None:
            return ActionResult(success=False, error="Key and duration are required", error_code="MISSING_PARAM")
        try:
            kb = _get_keyboard(context)
            if hasattr(kb, "hold"):
                kb.hold(key, duration)
            else:
                kb.hold_key(key, duration)
            return ActionResult(success=True, data={"key": key, "duration": duration, "completed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


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
            kb = _get_keyboard(context)
            if hasattr(kb, "release_all"):
                kb.release_all()
            else:
                kb.release_all_keys()
            return ActionResult(success=True, data={"released": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class PressKeys(Action):
    name = "press_keys"
    description = "Press multiple keys in sequence"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {"keys": {"type": "list", "required": True, "description": "List of key strings"}}

    def execute(self, context, parameters):
        p = parameters or {}
        keys = p.get("keys")
        if not isinstance(keys, list):
            return ActionResult(success=False, error="Keys must be a list", error_code="INVALID_INPUT")
        try:
            kb = _get_keyboard(context)
            if hasattr(kb, "press_sequence"):
                kb.press_sequence(keys)
            else:
                kb.press_keys(keys)
            return ActionResult(success=True, data={"keys": keys, "count": len(keys)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class TypeText(Action):
    name = "type_text"
    description = "Type a string of text into the active application"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {"text": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        p = parameters or {}
        if "text" not in p or p.get("text") is None:
            return ActionResult(success=False, error="Parameter 'text' is required", error_code="MISSING_PARAM")
        text = p.get("text")
        try:
            kb = _get_keyboard(context)
            if hasattr(kb, "type"):
                kb.type(text)
            else:
                kb.type_text(text)
            return ActionResult(success=True, data={"text_length": len(text), "typed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class TypeTextSlowly(Action):
    name = "type_text_slowly"
    description = "Type text with a delay between characters"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "text": {"type": "string", "required": True},
        "interval": {"type": "float", "required": False, "default": 0.05},
    }

    def execute(self, context, parameters):
        p = parameters or {}
        if "text" not in p or p.get("text") is None:
            return ActionResult(success=False, error="Parameter 'text' is required", error_code="MISSING_PARAM")
        text = p.get("text")
        interval = p.get("interval", 0.05)
        try:
            kb = _get_keyboard(context)
            if hasattr(kb, "type"):
                kb.type(text, interval=interval)
            else:
                kb.type_text_slowly(text, interval)
            return ActionResult(success=True, data={"text_length": len(text), "interval": interval, "typed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class PasteText(Action):
    name = "paste_text"
    description = "Paste text using clipboard (better for long or special character strings)"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {"text": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        p = parameters or {}
        if "text" not in p or p.get("text") is None:
            return ActionResult(success=False, error="Parameter 'text' is required", error_code="MISSING_PARAM")
        text = p.get("text")
        try:
            cb = _get_clipboard(context)
            if hasattr(cb, "set_clipboard"):
                cb.set_clipboard(text)
            else:
                cb.copy(text)

            kb = _get_keyboard(context)
            if hasattr(kb, "paste"):
                kb.paste()
            else:
                kb.paste_text(text)
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
            kb = _get_keyboard(context)
            if hasattr(kb, "copy"):
                kb.copy()
            else:
                kb.copy_selection()
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
            kb = _get_keyboard(context)
            if hasattr(kb, "cut"):
                kb.cut()
            else:
                kb.cut_selection()
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
            kb = _get_keyboard(context)
            if hasattr(kb, "select_all"):
                kb.select_all()
            else:
                kb.select_all()
            return ActionResult(success=True, data={"selected": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class DeleteSelection(Action):
    name = "delete_selection"
    description = "Delete currently selected content"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = True
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            kb = _get_keyboard(context)
            if hasattr(kb, "delete"):
                kb.delete()
            else:
                kb.delete_selection()
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
            kb = _get_keyboard(context)
            if hasattr(kb, "get_state"):
                state = kb.get_state()
            else:
                state = kb.get_keyboard_state()
            return ActionResult(success=True, data=state)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))
