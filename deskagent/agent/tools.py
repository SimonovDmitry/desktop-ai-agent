from copy import deepcopy
from pathlib import Path
from typing import Any

from deskagent.actions.base import ActionRegistry
from deskagent.actions.executor import ActionExecutor
from deskagent.agent.llm.response import ToolCall
from deskagent.agent.models import ActionExecution
from deskagent.agent.policy import ActionPolicy

def create_mvp_action_registry() -> ActionRegistry:
    from deskagent.actions.application.information import (
        GetActiveApplication, GetApplicationStatus, GetRunningApplications,
    )
    from deskagent.actions.application.lifecycle import LaunchApplication, LaunchOrActivateApplication
    from deskagent.actions.system.audio import (
        DecreaseVolume, GetVolume, IncreaseVolume, Mute, SetVolume, Unmute,
    )
    from deskagent.actions.system.information import GetBatteryStatus, GetCurrentDate, GetCurrentTime
    from deskagent.actions.system.notification import SendNotification

    action_classes = (
        LaunchApplication, LaunchOrActivateApplication, GetRunningApplications,
        GetActiveApplication, GetApplicationStatus, SetVolume, IncreaseVolume,
        DecreaseVolume, Mute, Unmute, GetVolume, GetBatteryStatus,
        GetCurrentTime, GetCurrentDate, SendNotification,
    )
    registry = ActionRegistry()
    for action_class in action_classes:
        registry.register(action_class)
    return registry


class ActionToolCatalog:
    def __init__(self, registry: ActionRegistry, executor: ActionExecutor, context, allowed_names=None, policy=None, verifier=None):
        self.registry = registry
        self.executor = executor
        self.context = context
        self.allowed_names = self._resolve_names(allowed_names)
        self.policy = policy or ActionPolicy()
        self.verifier = verifier

    def _resolve_names(self, names):
        requested = names if names is not None else self.registry.names()
        available = [name for name in requested if self.registry.contains(name)]
        if not available:
            raise ValueError("No allowed actions are registered")
        return tuple(available)

    def schemas(self, names=None) -> list[dict[str, Any]]:
        selected = names or self.allowed_names
        return [self._action_to_schema(self.registry.get(name)) for name in selected if name in self.allowed_names]

    def policy_for(self, tool_call: ToolCall, action_count=0):
        if tool_call.name not in self.allowed_names:
            from deskagent.agent.policy import PolicyDecision
            return PolicyDecision(False, reason=f"Action is not allowed: {tool_call.name}")
        return self.policy.evaluate(self.registry.get(tool_call.name), tool_call.arguments, action_count)

    def execute(self, tool_call: ToolCall) -> ActionExecution:
        if tool_call.name not in self.allowed_names:
            return ActionExecution(
                tool_call_id=tool_call.id, name=tool_call.name, parameters=tool_call.arguments,
                success=False, error=f"Action is not allowed: {tool_call.name}", error_code="ACTION_NOT_ALLOWED",
            )
        result = self.executor.execute(tool_call.name, self.context, tool_call.arguments)
        return ActionExecution(
            tool_call_id=tool_call.id, name=tool_call.name, parameters=tool_call.arguments,
            success=result.success, data=result.data, error=result.error, error_code=result.error_code,
        )

    def verify(self, execution: ActionExecution) -> ActionExecution:
        if isinstance(execution.data, dict) and execution.data.get("dry_run"):
            return ActionExecution(**{**execution.to_dict(), "verified": True})
        verified, error = execution.success, None
        if execution.success and self.verifier:
            try:
                result = self.verifier(execution, self.context)
                verified, error = (result if isinstance(result, tuple) else (bool(result), None))
            except Exception as exc:
                verified, error = False, str(exc)
        elif execution.success:
            verified, error = self._verify_builtin(execution)
        return ActionExecution(**{
            **execution.to_dict(), "verified": verified,
            "verification_error": error,
        })

    def _verify_builtin(self, execution):
        try:
            if execution.name in ("launch_application", "launch_or_activate_application"):
                app = execution.parameters.get("application")
                return bool(self.context.services.application.information.is_running(app)), None
            if execution.name in ("quit_application", "force_quit_application"):
                app = execution.parameters.get("application")
                stopped = not self.context.services.application.information.is_running(app)
                return stopped, None if stopped else f"Application is still running: {app}"
            if execution.name == "set_volume":
                actual = self.context.services.system.audio.get_volume()
                expected = execution.parameters.get("volume")
                return actual == expected, None if actual == expected else f"Expected volume {expected}, got {actual}"
            file_result = self._verify_file(execution)
            if file_result:
                return file_result
            return True, None
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _verify_file(execution):
        name, parameters, data = execution.name, execution.parameters, execution.data or {}
        if name in {"delete_file", "trash_file"}:
            exists = Path(parameters["path"]).expanduser().exists()
            return not exists, None if not exists else "File still exists"
        if name == "move_file":
            source, target = Path(parameters["source"]).expanduser(), Path(parameters["destination"]).expanduser()
            valid = not source.exists() and target.exists()
            return valid, None if valid else "Move result does not match the filesystem"
        targets = {
            "create_file": parameters.get("path"), "write_file": parameters.get("path"),
            "write_text_file": parameters.get("path"), "copy_file": parameters.get("destination"),
            "rename_file": data.get("new_path"), "duplicate_file": data.get("destination"),
        }
        target = targets.get(name)
        if target:
            exists = Path(target).expanduser().exists()
            return exists, None if exists else f"Expected file does not exist: {target}"
        return None

    @classmethod
    def _action_to_schema(cls, action_class) -> dict[str, Any]:
        properties, required = {}, []
        for name, parameter in action_class.parameters_schema.items():
            properties[name] = cls._parameter_to_schema(parameter)
            if parameter.get("required"):
                required.append(name)

        parameters = {"type": "object", "properties": properties, "additionalProperties": False}
        if required:
            parameters["required"] = required

        return {
            "type": "function",
            "function": {
                "name": action_class.name,
                "description": action_class.description,
                "parameters": parameters,
            },
        }

    @staticmethod
    def _parameter_to_schema(parameter: dict[str, Any]) -> dict[str, Any]:
        schema = deepcopy(parameter)
        schema.pop("required", None)
        type_name = schema.pop("type", "string")
        type_mapping = {
            "string": {"type": "string"},
            "integer": {"type": "integer"},
            "float": {"type": "number"},
            "boolean": {"type": "boolean"},
            "list": {"type": "array", "items": {}},
            "dict": {"type": "object"},
            "string_or_int": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
        }
        result = type_mapping.get(type_name, {"type": "string"})
        for key in ("description", "default", "minimum", "maximum", "enum", "items"):
            if key in schema:
                result[key] = schema[key]
        return result
