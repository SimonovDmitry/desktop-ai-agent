import logging
from dataclasses import dataclass

from deskagent.actions.base import ActionRegistry
from deskagent.actions.executor import ActionExecutor
from deskagent.agent.agent import DesktopAgent
from deskagent.agent.graph import AgentGraph
from deskagent.agent.llm.base import LLMProvider
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.factory import create_llm
from deskagent.agent.tools import ActionToolCatalog, create_mvp_action_registry
from deskagent.core.config import Settings
from deskagent.core.context import ActionContext
from deskagent.core.services import ServicesFactory


@dataclass
class AgentRuntime:
    llm: LLMProvider
    registry: ActionRegistry
    executor: ActionExecutor
    context: object

    def create_agent(self, allowed_actions=None, max_iterations=6) -> DesktopAgent:
        tools = ActionToolCatalog(self.registry, self.executor, self.context, allowed_actions)
        return DesktopAgent(AgentGraph(self.llm, tools, max_iterations=max_iterations))


def create_desktop_agent(llm_config: LLMConfig | None = None, allowed_actions=None, max_iterations=6, confirmation_handler=None):
    registry = create_mvp_action_registry()
    context = ActionContext(
        settings=Settings(),
        logger=logging.getLogger("deskagent"),
        services=ServicesFactory.create(),
    )
    executor = ActionExecutor(registry=registry, confirmation_handler=confirmation_handler)
    runtime = AgentRuntime(llm=create_llm(llm_config), registry=registry, executor=executor, context=context)
    return runtime.create_agent(allowed_actions=allowed_actions, max_iterations=max_iterations)
