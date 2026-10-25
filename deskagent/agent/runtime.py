from dataclasses import dataclass

from deskagent.actions.base import ActionRegistry
from deskagent.actions.executor import ActionExecutor
from deskagent.agent.agent import DesktopAgent
from deskagent.agent.graph import AgentGraph
from deskagent.agent.llm.base import LLMProvider
from deskagent.agent.tools import ActionToolCatalog


@dataclass
class AgentRuntime:
    llm: LLMProvider
    registry: ActionRegistry
    executor: ActionExecutor
    context: object

    def create_agent(
        self,
        allowed_actions=None,
        max_iterations=6,
    ) -> DesktopAgent:
        tools = ActionToolCatalog(
            registry=self.registry,
            executor=self.executor,
            context=self.context,
            allowed_names=allowed_actions,
        )
        graph = AgentGraph(
            llm=self.llm,
            tools=tools,
            max_iterations=max_iterations,
        )
        return DesktopAgent(graph)
