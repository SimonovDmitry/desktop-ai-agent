from copy import deepcopy
from typing import Any

from deskagent.actions.base import ActionRegistry
from deskagent.actions.executor import ActionExecutor
from deskagent.agent.llm.response import ToolCall
from deskagent.agent.models import ActionExecution


DEFAULT_ACTION_NAMES = (
    "launch_application",
    "launch_or_activate_application",
    "get_running_applications",
    "get_active_application",
    "get_application_status",
    "set_volume",
    "increase_volume",
    "decrease_volume",
    "mute",
    "unmute",
    "get_volume",
    "get_battery_status",
    "get_current_time",
    "get_current_date",
    "send_notification",
)


def create_mvp_action_registry() -> ActionRegistry:
    from deskagent.actions.application.information import (
        GetActiveApplication,
        GetApplicationStatus,
        GetRunningApplications,
    )
    from deskagent.actions.application.lifecycle import (
        LaunchApplication,
        LaunchOrActivateApplication,
    )
    from deskagent.actions.system.audio import (
        DecreaseVolume,
        GetVolume,
        IncreaseVolume,
        Mute,
        SetVolume,
        Unmute,
    )
    from deskagent.actions.system.information import (
        GetBatteryStatus,
        GetCurrentDate,
        GetCurrentTime,
    )
    from deskagent.actions.system.notification import SendNotification

    action_classes = (
        LaunchApplication,
        LaunchOrActivateApplication,
        GetRunningApplications,
        GetActiveApplication,
        GetApplicationStatus,
        SetVolume,
        IncreaseVolume,
        DecreaseVolume,
        Mute,
        Unmute,
        GetVolume,
        GetBatteryStatus,
        GetCurrentTime,
        GetCurrentDate,
        SendNotification,
    )
    registry = ActionRegistry()
    for action_class in action_classes:
        registry.register(action_class)
    return registry


class ActionToolCatalog:
    def __init__(
        self,
        registry: ActionRegistry,
        executor: ActionExecutor,
        context,
        allowed_names: list[str] | tuple[str, ...] | None = None,
    ):
        self.registry = registry
        self.executor = executor
        self.context = context
        self.allowed_names = self._resolve_names(allowed_names)

    def _resolve_names(self, names):
        requested = names or DEFAULT_ACTION_NAMES
        available = []

        for name in requested:
            if self.registry.contains(name):
                available.append(name)

        if not available:
            raise ValueError("No allowed actions are registered")

        return tuple(available)

    def schemas(self) -> list[dict[str, Any]]:
        return [
            self._action_to_schema(self.registry.get(name))
            for name in self.allowed_names
        ]

    def execute(self, tool_call: ToolCall) -> ActionExecution:
        if tool_call.name not in self.allowed_names:
            return ActionExecution(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                parameters=tool_call.arguments,
                success=False,
                error=f"Action is not allowed: {tool_call.name}",
                error_code="ACTION_NOT_ALLOWED",
            )

        result = self.executor.execute(
            tool_call.name,
            self.context,
            tool_call.arguments,
        )

        return ActionExecution(
            tool_call_id=tool_call.id,
            name=tool_call.name,
            parameters=tool_call.arguments,
            success=result.success,
            data=result.data,
            error=result.error,
            error_code=result.error_code,
        )

    @classmethod
    def _action_to_schema(cls, action_class) -> dict[str, Any]:
        properties = {}
        required = []

        for name, parameter in action_class.parameters_schema.items():
            properties[name] = cls._parameter_to_schema(parameter)
            if parameter.get("required"):
                required.append(name)

        parameters = {
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
        }
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
            "string_or_int": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "integer"},
                ]
            },
        }
        result = type_mapping.get(type_name, {"type": "string"})

        for key in (
            "description",
            "default",
            "minimum",
            "maximum",
            "enum",
            "items",
        ):
            if key in schema:
                result[key] = schema[key]

        return result
