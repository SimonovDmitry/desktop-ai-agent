import json
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]
    id: str = field(default_factory=lambda: f"call_{uuid.uuid4().hex}")

    @classmethod
    def from_value(cls, value: Any) -> "ToolCall":
        if isinstance(value, cls):
            return value

        if isinstance(value, dict):
            function = value.get("function", value)
            name = function.get("name", value.get("name", ""))
            arguments = function.get("arguments", value.get("args", {}))
            call_id = value.get("id") or f"call_{uuid.uuid4().hex}"
        else:
            function = getattr(value, "function", value)
            name = getattr(function, "name", getattr(value, "name", ""))
            arguments = getattr(function, "arguments", getattr(value, "args", {}))
            call_id = getattr(value, "id", None) or f"call_{uuid.uuid4().hex}"

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

        return cls(id=call_id, name=name, arguments=arguments or {})


@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    thinking: str | None = None
    finish_reason: str | None = None
    raw: Any = None

    def __post_init__(self):
        self.tool_calls = [ToolCall.from_value(tc) for tc in self.tool_calls]
