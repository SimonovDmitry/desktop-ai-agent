import uuid
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
    verified: bool | None = None
    verification_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_call_id": self.tool_call_id, "name": self.name, "parameters": self.parameters,
            "success": self.success, "data": self.data, "error": self.error,
            "error_code": self.error_code, "verified": self.verified,
            "verification_error": self.verification_error,
        }

    def tool_result(self) -> dict[str, Any]:
        return {key: self.to_dict()[key] for key in (
            "success", "data", "error", "error_code", "verified", "verification_error",
        )}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ActionExecution":
        return cls(**{key: value.get(key) for key in cls.__dataclass_fields__})


@dataclass(frozen=True)
class PlanStep:
    id: str
    description: str
    action: str | None = None
    status: str = "pending"
    attempts: int = 0
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}


@dataclass(frozen=True)
class AgentResponse:
    content: str
    actions: list[ActionExecution] = field(default_factory=list)
    thread_id: str | None = None
    error: str | None = None
    pending_confirmation: dict[str, Any] | None = None
    plan: list[dict[str, Any]] = field(default_factory=list)

    @property
    def interrupted(self) -> bool:
        return self.pending_confirmation is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content, "actions": [action.to_dict() for action in self.actions],
            "thread_id": self.thread_id, "error": self.error,
            "pending_confirmation": self.pending_confirmation, "plan": self.plan,
        }


@dataclass
class AgentSession:
    thread_id: str = field(default_factory=lambda: f"session_{uuid.uuid4().hex}")

    def graph_config(self) -> dict:
        return {"configurable": {"thread_id": self.thread_id}}
