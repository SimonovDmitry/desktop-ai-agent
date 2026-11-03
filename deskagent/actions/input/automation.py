import time

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


def _get_keyboard(context):
    if hasattr(context.services, "system") and hasattr(context.services.system, "keyboard"):
        return context.services.system.keyboard
    if hasattr(context.services, "input") and hasattr(context.services.input, "keyboard"):
        return context.services.input.keyboard
    return getattr(context.services, "keyboard", None)


def _get_mouse(context):
    if hasattr(context.services, "system") and hasattr(context.services.system, "mouse"):
        return context.services.system.mouse
    if hasattr(context.services, "input") and hasattr(context.services.input, "mouse"):
        return context.services.input.mouse
    return getattr(context.services, "mouse", None)


def _get_monitor(context):
    if hasattr(context.services, "system") and hasattr(context.services.system, "input_monitor"):
        return context.services.system.input_monitor
    if hasattr(context.services, "input") and hasattr(context.services.input, "monitor"):
        return context.services.input.monitor
    return getattr(context.services, "input_monitor", None)


def _run_action_item(context, act):
    act_type = act.get("type")
    kb = _get_keyboard(context)
    mouse = _get_mouse(context)
    if act_type == "move_mouse":
        if mouse and hasattr(mouse, "move_mouse"):
            mouse.move_mouse(act.get("x"), act.get("y"))
    elif act_type == "click":
        if mouse and hasattr(mouse, "click"):
            if "button" in act:
                mouse.click(act["button"])
            else:
                mouse.click()
    elif act_type == "type_text":
        if kb and hasattr(kb, "type"):
            kb.type(act.get("text"))
    elif act_type == "press_key":
        if kb:
            fn = getattr(kb, "press_key", getattr(kb, "press", None))
            if fn:
                fn(act.get("key"))
    elif act_type == "tap_key":
        if kb:
            fn = getattr(kb, "tap_key", getattr(kb, "tap", None))
            if fn:
                fn(act.get("key"))


class ExecuteInputSequence(Action):
    name = "execute_input_sequence"
    description = "Execute a list of various input actions (mouse movement, clicks, typing) in order"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "actions": {
            "type": "list",
            "required": True,
            "description": "List of action objects like {'type': 'click', 'button': 'left'}",
        }
    }

    def execute(self, context, parameters):
        actions = parameters.get("actions", [])
        if hasattr(context.services, "input") and hasattr(context.services.input, "automation"):
            try:
                result = context.services.input.automation.execute_input_sequence(actions)
                return ActionResult(success=result.get("completed", True), data=result)
            except Exception as exc:
                return ActionResult(success=False, error=str(exc))

        executed = 0
        try:
            for act in actions:
                _run_action_item(context, act)
                executed += 1
            return ActionResult(success=True, data={"completed": True, "executed": executed, "failed": 0})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), data={"executed": executed})


class ExecuteInputSequenceWithDelay(Action):
    name = "execute_input_sequence_with_delay"
    description = "Execute a list of input actions with a fixed delay between each step"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "actions": {"type": "list", "required": True},
        "delay": {"type": "float", "required": False, "default": 0.5},
    }

    def execute(self, context, parameters):
        actions = parameters.get("actions", [])
        delay = parameters.get("delay", 0.5)

        if hasattr(context.services, "input") and hasattr(context.services.input, "automation"):
            try:
                result = context.services.input.automation.execute_input_sequence_with_delay(actions, delay)
                return ActionResult(success=True, data=result)
            except Exception as exc:
                return ActionResult(success=False, error=str(exc))

        try:
            for act in actions:
                _run_action_item(context, act)
                time.sleep(delay)
            return ActionResult(success=True, data={"executed": len(actions)})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class WaitForInput(Action):
    name = "wait_for_input"
    description = "Pause execution until any input event occurs (mouse or keyboard)"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "input_type": {"type": "string", "required": False, "enum": ["mouse_click", "key_press", "any"]},
        "timeout": {"type": "integer", "required": False, "default": 30},
    }

    def execute(self, context, parameters):
        itype = parameters.get("input_type", "any")
        timeout = parameters.get("timeout", 30)
        try:
            if hasattr(context.services, "input") and hasattr(context.services.input, "automation"):
                result = context.services.input.automation.wait_for_input(itype, timeout)
                return ActionResult(success=True, data=result)
            monitor = _get_monitor(context)
            if monitor and hasattr(monitor, "wait_for_event"):
                monitor.wait_for_event(itype, timeout)
            return ActionResult(success=True, data={"triggered": True, "input_type": itype})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="TIMEOUT")


class WaitForKey(Action):
    name = "wait_for_key"
    description = "Pause execution until a specific key is pressed by the user"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "key": {"type": "string", "required": True},
        "timeout": {"type": "integer", "required": False, "default": 10},
    }

    def execute(self, context, parameters):
        key = parameters.get("key")
        timeout = parameters.get("timeout", 10)
        try:
            if hasattr(context.services, "input") and hasattr(context.services.input, "automation"):
                result = context.services.input.automation.wait_for_key(key, timeout)
                return ActionResult(success=True, data=result)
            kb = _get_keyboard(context)
            if kb and hasattr(kb, "wait_for_key"):
                kb.wait_for_key(key, timeout)
            return ActionResult(success=True, data={"key": key, "pressed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class WaitForMouseClick(Action):
    name = "wait_for_mouse_click"
    description = "Pause execution until a mouse click is detected"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "button": {"type": "string", "required": False, "default": "left"},
        "timeout": {"type": "integer", "required": False, "default": 10},
    }

    def execute(self, context, parameters):
        btn = parameters.get("button", "left")
        timeout = parameters.get("timeout", 10)
        try:
            if hasattr(context.services, "input") and hasattr(context.services.input, "automation"):
                result = context.services.input.automation.wait_for_mouse_click(btn, timeout)
                return ActionResult(success=True, data=result)
            mouse = _get_mouse(context)
            pos = None
            if mouse and hasattr(mouse, "wait_for_click"):
                pos = mouse.wait_for_click(btn, timeout)
            return ActionResult(success=True, data={"button": btn, "clicked_at": pos})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class RepeatInputAction(Action):
    name = "repeat_input_action"
    description = "Repeat a single input action multiple times"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "action": {"type": "dict", "required": True, "description": "The action to repeat"},
        "count": {"type": "integer", "required": True},
        "interval": {"type": "float", "required": False, "default": 0.1},
    }

    def execute(self, context, parameters):
        action_data = parameters.get("action")
        count = parameters.get("count")
        interval = parameters.get("interval", 0.1)

        try:
            if hasattr(context.services, "input") and hasattr(context.services.input, "automation"):
                result = context.services.input.automation.repeat_input_action(action_data, count, interval)
                return ActionResult(success=True, data=result)
            for _ in range(count):
                _run_action_item(context, action_data)
                time.sleep(interval)
            return ActionResult(success=True, data={"executed": count, "completed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class CancelInputAutomation(Action):
    name = "cancel_input_automation"
    description = "Stop any currently running input sequences or wait operations"
    category = ActionCategory.SYSTEM
    parameters_schema = {"automation_id": {"type": "string", "required": False}}

    def execute(self, context, parameters):
        auto_id = parameters.get("automation_id")
        try:
            if hasattr(context.services, "input") and hasattr(context.services.input, "automation"):
                result = context.services.input.automation.cancel_input_automation(auto_id)
                return ActionResult(success=True, data=result)
            kb = _get_keyboard(context)
            mouse = _get_mouse(context)
            if kb and hasattr(kb, "stop_automation"):
                kb.stop_automation(auto_id)
            if mouse and hasattr(mouse, "stop_automation"):
                mouse.stop_automation(auto_id)
            return ActionResult(success=True, data={"automation_id": auto_id, "cancelled": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))
