import json
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from deskagent.agent.llm.base import LLMProvider, LLMProviderError
from deskagent.agent.llm.response import ToolCall
from deskagent.agent.models import ActionExecution, AgentState
from deskagent.agent.tools import ActionToolCatalog

SYSTEM_PROMPT = """
You are DeskAgent, a local desktop assistant for macOS.
Use tools for computer actions and trust only their confirmed results.
Never invent system state, paths or successful actions.
Report tool errors briefly, stop when the task is complete and answer in the user's language.
""".strip()


class AgentGraph:
    def __init__(self, llm: LLMProvider, tools: ActionToolCatalog, max_iterations: int = 6, max_tool_calls_per_iteration: int = 4, checkpointer=None):
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        self.llm = llm
        self.tools = tools
        self.max_iterations = max_iterations
        self.max_tool_calls_per_iteration = max_tool_calls_per_iteration
        self.graph = self._build_graph(checkpointer or InMemorySaver())

    def _build_graph(self, checkpointer):
        builder = StateGraph(AgentState)
        builder.add_node("model", self._call_model)
        builder.add_node("tools", self._execute_tools)
        builder.add_edge(START, "model")
        builder.add_conditional_edges("model", self._route_after_model, {"tools": "tools", "end": END})
        builder.add_edge("tools", "model")
        return builder.compile(checkpointer=checkpointer)

    def _call_model(self, state: AgentState) -> dict[str, Any]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *state.get("messages", [])]
        iterations = state.get("iterations", 0) + 1
        try:
            response = self.llm.generate(messages, tools=self.tools.schemas())
        except LLMProviderError as exc:
            return {"messages": [{"role": "assistant", "content": str(exc)}], "iterations": iterations, "error": str(exc)}

        if response.tool_calls and iterations >= self.max_iterations:
            error = "Agent stopped after reaching the maximum number of iterations"
            return {"messages": [{"role": "assistant", "content": error}], "iterations": iterations, "error": "MAX_ITERATIONS"}

        message = {"role": "assistant", "content": response.content}
        if response.tool_calls:
            message["tool_calls"] = [
                {"id": tc.id, "name": tc.name, "args": tc.arguments, "type": "tool_call"}
                for tc in response.tool_calls
            ]
        return {"messages": [message], "iterations": iterations, "error": None}

    def _route_after_model(self, state: AgentState) -> str:
        if state.get("error") or state.get("iterations", 0) >= self.max_iterations:
            return "end"
        return "tools" if self._tool_calls_from_last_message(state) else "end"

    def _execute_tools(self, state: AgentState) -> dict[str, Any]:
        tool_calls = self._tool_calls_from_last_message(state)
        executions = []
        for index, tool_call in enumerate(tool_calls):
            if index < self.max_tool_calls_per_iteration:
                executions.append(self.tools.execute(tool_call))
            else:
                executions.append(ActionExecution(
                    tool_call_id=tool_call.id, name=tool_call.name, parameters=tool_call.arguments,
                    success=False, error="Tool call limit exceeded", error_code="TOOL_CALL_LIMIT",
                ))

        messages = [
            {
                "role": "tool",
                "name": ex.name,
                "tool_call_id": ex.tool_call_id,
                "content": json.dumps(ex.to_dict(), ensure_ascii=False, default=str),
            }
            for ex in executions
        ]
        return {"messages": messages, "action_executions": executions}

    @staticmethod
    def _tool_calls_from_last_message(state: AgentState) -> list[ToolCall]:
        messages = state.get("messages", [])
        if not messages:
            return []
        msg = messages[-1]
        values = msg.get("tool_calls", []) if isinstance(msg, dict) else getattr(msg, "tool_calls", [])
        return [ToolCall.from_value(v) for v in values]
