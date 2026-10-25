from operator import add
from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages

from deskagent.agent.models import ActionExecution


class AgentState(TypedDict, total=False):
    messages: Annotated[list[Any], add_messages]
    action_executions: Annotated[list[ActionExecution], add]
    iterations: int
    error: str | None
