from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


def _get_keyboard(context):
    if hasattr(context.services, "system") and hasattr(context.services.system, "keyboard"):
        return context.services.system.keyboard
    if hasattr(context.services, "input") and hasattr(context.services.input, "state"):
        return context.services.input.state
    return getattr(context.services, "keyboard", None)


def _get_mouse(context):
    if hasattr(context.services, "system") and hasattr(context.services.system, "mouse"):
        return context.services.system.mouse
    if hasattr(context.services, "input") and hasattr(context.services.input, "state"):
        return context.services.input.state
    return getattr(context.services, "mouse", None)


class GetKeyboardState(Action):
    discoverable = False
    name = "get_keyboard_state"
    description = "Get the current state of modifier keys (shift, cmd, etc.)"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            if hasattr(context.services, "input") and hasattr(context.services.input, "state"):
                state = context.services.input.state.get_keyboard_state()
            else:
                kb = _get_keyboard(context)
                state = kb.get_state() if hasattr(kb, "get_state") else {}
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
            kb = _get_keyboard(context)
            keys = kb.get_pressed_keys()
            return ActionResult(success=True, data={"keys": keys, "count": len(keys)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsKeyPressed(Action):
    name = "is_key_pressed"
    description = "Check if a specific key is currently pressed"
    category = ActionCategory.SYSTEM
    parameters_schema = {"key": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        key = parameters.get("key")
        try:
            kb = _get_keyboard(context)
            method = getattr(kb, "is_pressed", getattr(kb, "is_key_pressed", None))
            is_pressed = method(key)
            return ActionResult(success=True, data={"key": key, "pressed": is_pressed})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetMouseButtonState(Action):
    discoverable = False
    name = "get_mouse_button_state"
    description = "Get current state of mouse buttons (left, right, middle)"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            mouse = _get_mouse(context)
            method = getattr(mouse, "get_button_state", getattr(mouse, "get_mouse_button_state", None))
            state = method()
            return ActionResult(success=True, data=state)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsMouseButtonPressed(Action):
    name = "is_mouse_button_pressed"
    description = "Check if a specific mouse button is currently held down"
    category = ActionCategory.SYSTEM
    parameters_schema = {"button": {"type": "string", "required": True, "enum": ["left", "right", "middle"]}}

    def execute(self, context, parameters):
        btn = parameters.get("button")
        try:
            mouse = _get_mouse(context)
            method = getattr(mouse, "is_pressed", getattr(mouse, "is_mouse_button_pressed", None))
            is_pressed = method(btn)
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
            if (
                hasattr(context.services, "input")
                and hasattr(context.services.input, "state")
                and hasattr(context.services.input.state, "get_input_state")
            ):
                return ActionResult(success=True, data=context.services.input.state.get_input_state())
            kb = _get_keyboard(context)
            mouse = _get_mouse(context)
            kb_state = kb.get_state() if hasattr(kb, "get_state") else {}
            if isinstance(kb_state, dict) and "pressed_keys" in kb_state:
                kb_data = {"pressed_keys": kb_state["pressed_keys"]}
            else:
                kb_data = kb_state
            mouse_pos = mouse.get_cursor_position() if hasattr(mouse, "get_cursor_position") else None
            mouse_buttons = mouse.get_button_state() if hasattr(mouse, "get_button_state") else None
            mouse_data = {}
            if mouse_pos is not None:
                mouse_data["position"] = mouse_pos
            if mouse_buttons is not None:
                mouse_data["buttons"] = mouse_buttons
            return ActionResult(success=True, data={"keyboard": kb_data, "mouse": mouse_data})
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
            if (
                hasattr(context.services, "input")
                and hasattr(context.services.input, "state")
                and hasattr(context.services.input.state, "release_all_input")
            ):
                context.services.input.state.release_all_input()
            else:
                kb = _get_keyboard(context)
                mouse = _get_mouse(context)
                if hasattr(kb, "release_all"):
                    kb.release_all()
                if hasattr(mouse, "release_all"):
                    mouse.release_all()

            return ActionResult(
                success=True,
                data={"keys_released": True, "mouse_buttons_released": True},
            )
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="PANIC_RESET_FAILED")
