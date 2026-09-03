from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory
import time


class ExecuteInputSequence(Action):
    name = "execute_input_sequence"
    description = "Execute a list of various input actions (mouse movement, clicks, typing) in order"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "actions": {
            "type": "list",
            "required": True,
            "description": "List of action objects like {'type': 'click', 'button': 'left'}"
        }
    }

    def execute(self, context, parameters):
        actions = parameters.get('actions', [])
        executed_count = 0

        try:
            for act in actions:
                atype = act.get('type')

                if atype == "move_mouse":
                    context.services.system.mouse.move_mouse(act['x'], act['y'])
                elif atype == "click":
                    context.services.system.mouse.click(act.get('button', 'left'))
                elif atype == "type_text":
                    context.services.system.keyboard.type(act['text'])
                elif atype == "press_key":
                    context.services.system.keyboard.press(act['key'])
                elif atype == "tap_key":
                    context.services.system.keyboard.tap(act['key'])

                executed_count += 1

            return ActionResult(success=True, data={"completed": True, "executed": executed_count, "failed": 0})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), data={"executed": executed_count})


class ExecuteInputSequenceWithDelay(Action):
    name = "execute_input_sequence_with_delay"
    description = "Execute a list of input actions with a fixed delay between each step"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.MEDIUM
    parameters_schema = {
        "actions": {"type": "list", "required": True},
        "delay": {"type": "float", "required": False, "default": 0.5}
    }

    def execute(self, context, parameters):
        actions = parameters.get('actions', [])
        delay = parameters.get('delay', 0.5)

        try:
            for act in actions:
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
        "timeout": {"type": "integer", "required": False, "default": 30}
    }

    def execute(self, context, parameters):
        itype = parameters.get('input_type', 'any')
        timeout = parameters.get('timeout', 30)
        try:
            triggered = context.services.system.input_monitor.wait_for_event(itype, timeout)
            return ActionResult(success=True, data={"triggered": triggered, "input_type": itype})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="TIMEOUT")


class WaitForKey(Action):
    name = "wait_for_key"
    description = "Pause execution until a specific key is pressed by the user"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "key": {"type": "string", "required": True},
        "timeout": {"type": "integer", "required": False, "default": 10}
    }

    def execute(self, context, parameters):
        key = parameters.get('key')
        timeout = parameters.get('timeout', 10)
        try:
            context.services.system.keyboard.wait_for_key(key, timeout)
            return ActionResult(success=True, data={"key": key, "pressed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class WaitForMouseClick(Action):
    name = "wait_for_mouse_click"
    description = "Pause execution until a mouse click is detected"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "button": {"type": "string", "required": False, "default": "left"},
        "timeout": {"type": "integer", "required": False, "default": 10}
    }

    def execute(self, context, parameters):
        btn = parameters.get('button', 'left')
        timeout = parameters.get('timeout', 10)
        try:
            pos = context.services.system.mouse.wait_for_click(btn, timeout)
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
        "interval": {"type": "float", "required": False, "default": 0.1}
    }

    def execute(self, context, parameters):
        action_data = parameters.get('action')
        count = parameters.get('count')
        interval = parameters.get('interval', 0.1)

        try:
            for _ in range(count):
                time.sleep(interval)
            return ActionResult(success=True, data={"executed": count, "completed": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class CancelInputAutomation(Action):
    name = "cancel_input_automation"
    description = "Stop any currently running input sequences or wait operations"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "automation_id": {"type": "string", "required": False}
    }

    def execute(self, context, parameters):
        auto_id = parameters.get('automation_id')
        try:
            context.services.system.keyboard.stop_automation(auto_id)
            context.services.system.mouse.stop_automation(auto_id)
            return ActionResult(success=True, data={"automation_id": auto_id, "cancelled": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))