import uuid
from dataclasses import dataclass, field
from operator import add
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


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
        return {"success": self.success, "data": self.data, "error": self.error, "error_code": self.error_code}


@dataclass(frozen=True)
class AgentResponse:
    content: str
    actions: list[ActionExecution] = field(default_factory=list)
    thread_id: str | None = None
    error: str | None = None


@dataclass
class AgentSession:
    thread_id: str = field(default_factory=lambda: f"session_{uuid.uuid4().hex}")

    def graph_config(self) -> dict:
        return {"configurable": {"thread_id": self.thread_id}}


class AgentState(TypedDict, total=False):
    messages: Annotated[list[Any], add_messages]
    action_executions: Annotated[list[ActionExecution], add]
    iterations: int
    error: str | None
