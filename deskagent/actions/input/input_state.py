from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class GetKeyboardState(Action):
    name = "get_keyboard_state"
    description = "Get the current state of modifier keys (shift, cmd, etc.)"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            state = context.services.system.keyboard.get_state()
            return ActionResult(success=True, data=state)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetPressedKeys(Action):
    name = "get_pressed_keys"
    description = "Get a list of all keys currently being held down"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            keys = context.services.system.keyboard.get_pressed_keys()
            return ActionResult(success=True, data={"keys": keys, "count": len(keys)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsKeyPressed(Action):
    name = "is_key_pressed"
    description = "Check if a specific key is currently pressed"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "key": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        key = parameters.get('key')
        try:
            is_pressed = context.services.system.keyboard.is_pressed(key)
            return ActionResult(success=True, data={"key": key, "pressed": is_pressed})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetMouseButtonState(Action):
    name = "get_mouse_button_state"
    description = "Get current state of mouse buttons (left, right, middle)"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            state = context.services.system.mouse.get_button_state()
            return ActionResult(success=True, data=state)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsMouseButtonPressed(Action):
    name = "is_mouse_button_pressed"
    description = "Check if a specific mouse button is currently held down"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "button": {"type": "string", "required": True, "enum": ["left", "right", "middle"]}
    }

    def execute(self, context, parameters):
        btn = parameters.get('button')
        try:
            is_pressed = context.services.system.mouse.is_pressed(btn)
            return ActionResult(success=True, data={"button": btn, "pressed": is_pressed})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetInputState(Action):
    name = "get_input_state"
    description = "Get comprehensive state of all input devices (keyboard and mouse)"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            kb_state = context.services.system.keyboard.get_state()
            m_pos = context.services.system.mouse.get_cursor_position()
            m_buttons = context.services.system.mouse.get_button_state()

            return ActionResult(success=True, data={
                "keyboard": {
                    "pressed_keys": kb_state.get("pressed_keys", [])
                },
                "mouse": {
                    "position": m_pos,
                    "buttons": m_buttons
                }
            })
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class ReleaseAllInput(Action):
    name = "release_all_input"
    description = "Emergency reset: release all keys and mouse buttons to prevent stuck input"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            context.services.system.keyboard.release_all()
            context.services.system.mouse.release_all()

            return ActionResult(success=True, data={
                "keys_released": True,
                "mouse_buttons_released": True
            }, message="System input has been reset.")
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="PANIC_RESET_FAILED")