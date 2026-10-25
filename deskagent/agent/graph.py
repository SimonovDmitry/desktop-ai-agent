import json
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from deskagent.agent.llm.base import LLMProvider, LLMProviderError
from deskagent.agent.llm.response import ToolCall
from deskagent.agent.models import ActionExecution, PlanStep
from deskagent.agent.prompts import build_system_prompt
from deskagent.agent.routing import ToolRouter
from deskagent.agent.state import AgentState
from deskagent.agent.telemetry import Telemetry
from deskagent.agent.tools import ActionToolCatalog


class AgentGraph:
    def __init__(self, llm: LLMProvider, tools: ActionToolCatalog, max_iterations=8,
                 max_tool_calls_per_iteration=6, checkpointer=None, router=None, telemetry=None):
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        self.llm, self.tools = llm, tools
        self.max_iterations, self.max_tool_calls = max_iterations, max_tool_calls_per_iteration
        self.router, self.telemetry = router or ToolRouter(), telemetry or Telemetry()
        self.graph = self._build(checkpointer or InMemorySaver())

    def _build(self, checkpointer):
        graph = StateGraph(AgentState)
        for name, node in (
            ("route", self._route_tools), ("model", self._call_model),
            ("prepare", self._prepare_tools), ("approval", self._request_approval),
            ("tools", self._execute_tools), ("verify", self._verify),
        ):
            graph.add_node(name, node)
        graph.add_edge(START, "route")
        graph.add_edge("route", "model")
        graph.add_conditional_edges("model", self._after_model, {"prepare": "prepare", "end": END})
        graph.add_conditional_edges("prepare", self._after_prepare, {"approval": "approval", "tools": "tools"})
        graph.add_edge("approval", "tools")
        graph.add_edge("tools", "verify")
        graph.add_edge("verify", "model")
        return graph.compile(checkpointer=checkpointer)

    def _route_tools(self, state: AgentState):
        request = self._last_content(state, "human")
        selected = self.router.select(request, self.tools.registry, self.tools.allowed_names)
        self._emit("tools_selected", {"actions": selected})
        return {"selected_actions": selected}

    def _call_model(self, state: AgentState) -> dict[str, Any]:
        prompt = build_system_prompt(state.get("screen_context"), state.get("system_context"), state.get("plan"))
        messages = [{"role": "system", "content": prompt}, *state.get("messages", [])]
        iterations = state.get("iterations", 0) + 1
        try:
            with self.telemetry.span("llm", iteration=iterations):
                response = self.llm.generate(messages, tools=self.tools.schemas(state.get("selected_actions")))
        except LLMProviderError as exc:
            return {"messages": [{"role": "assistant", "content": str(exc)}], "iterations": iterations, "error": str(exc)}
        if response.tool_calls and iterations >= self.max_iterations:
            error = "Agent stopped after reaching the maximum number of iterations"
            return {"messages": [{"role": "assistant", "content": error}], "iterations": iterations, "error": "MAX_ITERATIONS"}
        if response.content:
            self._emit("token", response.content)
        message = {"role": "assistant", "content": response.content}
        if response.tool_calls:
            message["tool_calls"] = [self._call_dict(call) for call in response.tool_calls]
        return {"messages": [message], "iterations": iterations, "error": None}

    def _prepare_tools(self, state: AgentState):
        calls = self._tool_calls(state)[:self.max_tool_calls]
        pending, confirmations = [], []
        plan = list(state.get("plan", []))
        known_steps = {step.get("id") for step in plan}
        for call in calls:
            decision = self.tools.policy_for(call, state.get("action_count", 0) + len(pending))
            item = {**self._call_dict(call), "policy": decision.to_dict()}
            pending.append(item)
            if call.id not in known_steps:
                status = "waiting_confirmation" if decision.confirmation_required else "ready"
                plan.append(PlanStep(call.id, f"Run {call.name}", call.name, status=status).to_dict())
            if decision.allowed and decision.confirmation_required:
                confirmations.append({"id": call.id, "action": call.name, "parameters": call.arguments,
                                      "risk": self.tools.registry.get(call.name).risk_level.value})
        confirmation = None
        if confirmations:
            confirmation = {"question": "Approve dangerous actions?", "actions": confirmations}
        return {"pending_tool_calls": pending, "pending_confirmation": confirmation,
                "confirmation_approved": None, "plan": plan}

    def _request_approval(self, state: AgentState):
        payload = state.get("pending_confirmation") or {}
        self._emit("confirmation_needed", payload)
        answer = interrupt(payload)
        approved = answer.get("approved", False) if isinstance(answer, dict) else bool(answer)
        return {"confirmation_approved": approved}

    def _execute_tools(self, state: AgentState):
        executions, approved = [], state.get("confirmation_approved")
        for item in state.get("pending_tool_calls", []):
            call, policy = ToolCall.from_value(item), item.get("policy", {})
            if not policy.get("allowed", True):
                execution = self._failed(call, policy.get("reason"), "POLICY_DENIED")
            elif policy.get("confirmation_required") and not approved:
                execution = self._failed(call, "Action was not approved", "ACTION_CANCELLED")
            elif policy.get("dry_run"):
                execution = ActionExecution(call.id, call.name, call.arguments, True, {"dry_run": True})
            else:
                self._emit("action_started", {"id": call.id, "name": call.name, "parameters": call.arguments})
                with self.telemetry.span("action", action=call.name):
                    execution = self.tools.execute(call)
            executions.append(execution.to_dict())
            self._emit("action_finished", execution.to_dict())
        return {"current_executions": executions, "action_count": state.get("action_count", 0) + len(executions),
                "pending_confirmation": None, "confirmation_approved": None}

    def _verify(self, state: AgentState):
        verified, plan = [], list(state.get("plan", []))
        for value in state.get("current_executions", []):
            execution = self.tools.verify(ActionExecution.from_dict(value))
            verified.append(execution.to_dict())
            for step in plan:
                if step.get("id") == execution.tool_call_id:
                    step["attempts"] = step.get("attempts", 0) + 1
                    step["status"] = "completed" if execution.success and execution.verified else "failed"
        messages = [{"role": "tool", "name": item["name"], "tool_call_id": item["tool_call_id"],
                     "content": json.dumps(ActionExecution.from_dict(item).tool_result(), ensure_ascii=False, default=str)}
                    for item in verified]
        return {"messages": messages, "action_executions": verified, "current_executions": [], "plan": plan}

    def _after_model(self, state):
        if state.get("error") or state.get("iterations", 0) >= self.max_iterations:
            return "end"
        return "prepare" if self._tool_calls(state) else "end"

    @staticmethod
    def _after_prepare(state):
        return "approval" if state.get("pending_confirmation") else "tools"

    @staticmethod
    def _tool_calls(state):
        messages = state.get("messages", [])
        if not messages:
            return []
        message = messages[-1]
        values = message.get("tool_calls", []) if isinstance(message, dict) else getattr(message, "tool_calls", [])
        return [ToolCall.from_value(value) for value in values]

    @staticmethod
    def _call_dict(call):
        return {"id": call.id, "name": call.name, "args": call.arguments, "type": "tool_call"}

    @staticmethod
    def _failed(call, error, code):
        return ActionExecution(call.id, call.name, call.arguments, False, error=error, error_code=code)

    @staticmethod
    def _last_content(state, kind):
        for message in reversed(state.get("messages", [])):
            role = message.get("role") if isinstance(message, dict) else getattr(message, "type", None)
            if role in (kind, "user" if kind == "human" else kind):
                return str(message.get("content", "") if isinstance(message, dict) else message.content)
        return ""

    @staticmethod
    def _emit(event, data):
        try:
            get_stream_writer()({"event": event, "data": data})
        except RuntimeError:
            pass
