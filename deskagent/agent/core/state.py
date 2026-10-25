from operator import add
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    messages: Annotated[list[Any], add_messages]
    action_executions: Annotated[list[dict[str, Any]], add]
    current_executions: list[dict[str, Any]]
    selected_actions: list[str]
    pending_tool_calls: list[dict[str, Any]]
    pending_confirmation: dict[str, Any] | None
    confirmation_approved: bool | None
    thread_id: str
    screen_context: dict[str, Any]
    system_context: dict[str, Any]
    plan: list[dict[str, Any]]
    iterations: int
    action_count: int
    error: str | None
