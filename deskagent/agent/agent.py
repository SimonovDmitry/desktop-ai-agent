from typing import Any

from deskagent.agent.graph import AgentGraph
from deskagent.agent.models import AgentResponse, AgentSession


class ConversationManager:
    @staticmethod
    def user_message(content: str) -> dict[str, str]:
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
    def __init__(self, graph: AgentGraph, conversation: ConversationManager | None = None):
        self.graph = graph
        self.conversation = conversation or ConversationManager()

    def ask(self, request: str, session: AgentSession | None = None) -> AgentResponse:
        active_session = session or AgentSession()
        config = active_session.graph_config()
        previous_state = self.graph.graph.get_state(config)
        previous_actions = len(previous_state.values.get("action_executions", []))
        state = self.graph.graph.invoke(
            {
                "messages": [self.conversation.user_message(request)],
                "iterations": 0,
                "action_executions": [],
                "error": None,
            },
            config=config,
        )

        return AgentResponse(
            content=self.conversation.last_assistant_content(state.get("messages", [])),
            actions=state.get("action_executions", [])[previous_actions:],
            thread_id=active_session.thread_id,
            error=state.get("error"),
        )
