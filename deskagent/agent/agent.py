from deskagent.agent.conversation import ConversationManager
from deskagent.agent.graph import AgentGraph
from deskagent.agent.models import AgentResponse
from deskagent.agent.session import AgentSession


class DesktopAgent:
    def __init__(
        self,
        graph: AgentGraph,
        conversation: ConversationManager | None = None,
    ):
        self.graph = graph
        self.conversation = conversation or ConversationManager()

    def ask(
        self,
        request: str,
        session: AgentSession | None = None,
    ) -> AgentResponse:
        active_session = session or AgentSession()
        config = active_session.graph_config()
        previous_state = self.graph.graph.get_state(config)
        previous_actions = len(
            previous_state.values.get("action_executions", [])
        )
        state = self.graph.graph.invoke(
            {
                "messages": [
                    self.conversation.user_message(request)
                ],
                "iterations": 0,
                "action_executions": [],
                "error": None,
            },
            config=config,
        )

        return AgentResponse(
            content=self.conversation.last_assistant_content(
                state.get("messages", [])
            ),
            actions=state.get("action_executions", [])[previous_actions:],
            thread_id=active_session.thread_id,
            error=state.get("error"),
        )
