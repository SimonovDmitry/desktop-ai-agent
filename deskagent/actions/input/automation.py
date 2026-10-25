from deskagent.actions.base import Action
from deskagent.actions.types import RiskLevel, ActionCategory, ActionResult


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
        try:
            result = context.services.input.automation.execute_input_sequence(actions)
            return ActionResult(success=result.get("completed", True), data=result)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


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
            result = context.services.input.automation.execute_input_sequence_with_delay(actions, delay)
            return ActionResult(success=True, data=result)
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
            result = context.services.input.automation.wait_for_input(itype, timeout)
            return ActionResult(success=True, data=result)
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
            result = context.services.input.automation.wait_for_key(key, timeout)
            return ActionResult(success=True, data=result)
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
            result = context.services.input.automation.wait_for_mouse_click(btn, timeout)
            return ActionResult(success=True, data=result)
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
            result = context.services.input.automation.repeat_input_action(action_data, count, interval)
            return ActionResult(success=True, data=result)
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
            result = context.services.input.automation.cancel_input_automation(auto_id)
            return ActionResult(success=True, data=result)
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))
