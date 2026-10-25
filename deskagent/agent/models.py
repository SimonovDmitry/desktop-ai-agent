from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ActionExecution:
    tool_call_id: str
    name: str
    parameters: dict[str, Any]
    success: bool
    data: Any = None
    error: str | None = None
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_code": self.error_code,
        }


@dataclass(frozen=True)
class AgentResponse:
    content: str
    actions: list[ActionExecution] = field(default_factory=list)
    thread_id: str | None = None
    error: str | None = None
