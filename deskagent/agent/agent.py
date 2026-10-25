from typing import Any

from langgraph.types import Command

from deskagent.agent.core.graph import AgentGraph
from deskagent.agent.core.models import ActionExecution, AgentResponse, AgentSession


class ConversationManager:
    @staticmethod
    def user_message(content: str):
        text = content.strip()
        if not text:
            raise ValueError("User message cannot be empty")
        return {"role": "user", "content": text}

    @staticmethod
    def last_assistant_content(messages: list[Any]) -> str:
        for message in reversed(messages):
            role = message.get("role") if isinstance(message, dict) else getattr(message, "type", None)
            content = message.get("content", "") if isinstance(message, dict) else getattr(message, "content", "")
            if role in ("assistant", "ai") and content:
                return str(content)
        return ""


class DesktopAgent:
    def __init__(self, graph: AgentGraph, conversation=None, context_collector=None, memory=None,
                 event_bus=None, proactive_rules=None, skills=None):
        self.graph = graph
        self.conversation = conversation or ConversationManager()
        self.context_collector, self.memory = context_collector, memory
        self.event_bus, self.proactive_rules, self.skills = event_bus, proactive_rules, skills

    def ask(self, request: str, session: AgentSession | None = None, screen_context=None,
            system_context=None) -> AgentResponse:
        session = session or AgentSession()
        config, before = session.graph_config(), self.graph.graph.get_state(session.graph_config())
        if before.interrupts:
            return self._response(before, session.thread_id, len(before.values.get("action_executions", [])))
        previous = len(before.values.get("action_executions", []))
        state = self.graph.graph.invoke(self._input(request, screen_context, system_context), config=config)
        response = self._response(self.graph.graph.get_state(config), session.thread_id, previous, state)
        self._remember(request, response)
        return response

    def confirm(self, thread_id: str, approved=True) -> AgentResponse:
        session = AgentSession(thread_id)
        config, before = session.graph_config(), self.graph.graph.get_state(session.graph_config())
        if not before.interrupts:
            raise ValueError(f"Session is not waiting for confirmation: {thread_id}")
        previous = len(before.values.get("action_executions", []))
        state = self.graph.graph.invoke(Command(resume={"approved": approved}), config=config)
        return self._response(self.graph.graph.get_state(config), thread_id, previous, state)

    def resume(self, thread_id: str, value=True) -> AgentResponse:
        return self.confirm(thread_id, value)

    def poll_events(self, focus_mode=False):
        if not self.context_collector or not self.proactive_rules:
            return []
        screen, system = self.context_collector.collect()
        events = self.proactive_rules.evaluate(screen, system, focus_mode)
        if self.event_bus:
            for event in events:
                self.event_bus.publish(event)
        return events

    def stream_ask(self, request: str, session: AgentSession | None = None, screen_context=None,
                   system_context=None):
        session = session or AgentSession()
        config, snapshot = session.graph_config(), self.graph.graph.get_state(session.graph_config())
        previous = len(snapshot.values.get("action_executions", []))
        if snapshot.interrupts:
            yield {"event": "confirmation_needed", "data": snapshot.values.get("pending_confirmation")}
            return
        for chunk in self.graph.graph.stream(
            self._input(request, screen_context, system_context), config=config,
            stream_mode=("custom", "updates"), version="v2",
        ):
            event = self._stream_event(chunk)
            if event:
                yield event
        response = self._response(self.graph.graph.get_state(config), session.thread_id, previous)
        if response.interrupted:
            yield {"event": "confirmation_needed", "data": response.pending_confirmation}
        yield {"event": "done", "data": response.to_dict()}
        self._remember(request, response)

    def _input(self, request, screen_context=None, system_context=None):
        screen, system = self.context_collector.collect() if self.context_collector else ({}, {})
        screen.update(screen_context or {})
        system.update(system_context or {})
        return {
            "messages": [self.conversation.user_message(request)], "screen_context": screen,
            "system_context": system, "plan": [], "iterations": 0, "action_count": 0,
            "current_executions": [], "pending_tool_calls": [], "pending_confirmation": None,
            "confirmation_approved": None, "error": None,
        }

    def _response(self, snapshot, thread_id, previous=0, fallback=None):
        state = snapshot.values or fallback or {}
        actions = [ActionExecution.from_dict(value) for value in state.get("action_executions", [])[previous:]]
        return AgentResponse(
            self.conversation.last_assistant_content(state.get("messages", [])), actions, thread_id,
            state.get("error"), state.get("pending_confirmation") if snapshot.interrupts else None,
            state.get("plan", []),
        )

    @staticmethod
    def _stream_event(chunk):
        if isinstance(chunk, dict) and chunk.get("type") == "custom":
            return chunk.get("data")
        if isinstance(chunk, tuple) and len(chunk) == 2 and chunk[0] == "custom":
            return chunk[1]
        return None

    def _remember(self, request, response):
        if self.memory:
            self.memory.put("conversation", response.thread_id, {
                "request": request, "response": response.content, "plan": response.plan,
            })
