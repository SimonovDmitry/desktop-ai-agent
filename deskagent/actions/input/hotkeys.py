from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class RegisterHotkey(Action):
    name = "register_hotkey"
    description = "Register a global system hotkey to trigger a specific action"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = True
    parameters_schema = {
        "hotkey": {
            "type": "string",
            "required": True,
            "description": "Combination like 'cmd+shift+d'"
        },
        "action": {
            "type": "string",
            "required": True,
            "description": "Identifier of the action to execute"
        }
    }

    def execute(self, context, parameters):
        hotkey = parameters.get('hotkey')
        action_id = parameters.get('action')

        if not hotkey or not action_id:
            return ActionResult(success=False, error="Hotkey and action are required", error_code="MISSING_PARAM")

        try:
            context.services.system.keyboard.register_hotkey(hotkey, action_id)
            return ActionResult(success=True, data={"hotkey": hotkey, "registered": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class UnregisterHotkey(Action):
    name = "unregister_hotkey"
    description = "Remove a previously registered global hotkey"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "hotkey": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        hotkey = parameters.get('hotkey')
        try:
            context.services.system.keyboard.unregister_hotkey(hotkey)
            return ActionResult(success=True, data={"hotkey": hotkey, "unregistered": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class UnregisterAllHotkeys(Action):
    name = "unregister_all_hotkeys"
    description = "Remove all hotkeys registered by the agent"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            count = context.services.system.keyboard.unregister_all_hotkeys()
            return ActionResult(success=True, data={"removed": count})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class GetRegisteredHotkeys(Action):
    name = "get_registered_hotkeys"
    description = "Get a list of all currently active hotkeys managed by the agent"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        try:
            hotkeys = context.services.system.keyboard.get_registered_hotkeys()
            return ActionResult(success=True, data={"hotkeys": hotkeys})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class IsHotkeyRegistered(Action):
    name = "is_hotkey_registered"
    description = "Check if a specific hotkey is already in use by the agent"
    category = ActionCategory.SYSTEM
    parameters_schema = {
        "hotkey": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        hotkey = parameters.get('hotkey')
        try:
            is_reg = context.services.system.keyboard.is_hotkey_registered(hotkey)
            return ActionResult(success=True, data={"hotkey": hotkey, "registered": is_reg})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc))


class TriggerHotkey(Action):
    name = "trigger_hotkey"
    description = "Manually fire the action associated with a registered hotkey"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {
        "hotkey": {"type": "string", "required": True}
    }

    def execute(self, context, parameters):
        hotkey = parameters.get('hotkey')
        try:
            context.services.system.keyboard.trigger_hotkey(hotkey)
            return ActionResult(success=True, data={"hotkey": hotkey, "triggered": True})
        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="NOT_FOUND")