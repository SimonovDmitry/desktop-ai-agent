import logging
from dataclasses import dataclass

from deskagent.actions.base import ActionRegistry
from deskagent.actions.executor import ActionExecutor
from deskagent.actions.registry import create_action_registry
from deskagent.agent.agent import DesktopAgent
from deskagent.agent.checkpoints import create_checkpointer
from deskagent.agent.events import EventBus, ProactiveRules
from deskagent.agent.graph import AgentGraph
from deskagent.agent.llm.base import LLMProvider
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.factory import create_llm
from deskagent.agent.memory import MemoryStore
from deskagent.agent.perception import ContextCollector
from deskagent.agent.policy import ActionPolicy, PolicyConfig
from deskagent.agent.routing import ToolRouter
from deskagent.agent.skills import SkillStore
from deskagent.agent.telemetry import Telemetry
from deskagent.agent.tools import ActionToolCatalog
from deskagent.core.config import Settings
from deskagent.core.context import ActionContext
from deskagent.core.services import ServicesFactory


@dataclass
class AgentRuntime:
    llm: LLMProvider
    registry: ActionRegistry
    executor: ActionExecutor
    context: object

    def create_agent(self, allowed_actions=None, max_iterations=8, checkpointer=None, policy=None,
                     router=None, telemetry=None, memory=None, screen_provider=None,
                     event_bus=None, proactive_rules=None, skills=None):
        tools = ActionToolCatalog(self.registry, self.executor, self.context, allowed_actions, policy)
        graph = AgentGraph(self.llm, tools, max_iterations, checkpointer=checkpointer,
                           router=router, telemetry=telemetry)
        return DesktopAgent(
            graph, context_collector=ContextCollector(self.context, screen_provider), memory=memory,
            event_bus=event_bus, proactive_rules=proactive_rules, skills=skills,
        )


def create_desktop_agent(llm_config: LLMConfig, allowed_actions=None, max_iterations=8,
                         checkpoint_path=None, memory_path=None, telemetry_path=None,
                         policy_config: PolicyConfig | None = None, registry=None, screen_provider=None,
                         skills_path="~/.deskagent/skills"):
    registry = registry or create_action_registry()
    context = ActionContext(Settings(), logging.getLogger("deskagent"), ServicesFactory.create())
    executor = ActionExecutor(registry, confirmation_handler=lambda *_: True)
    runtime = AgentRuntime(create_llm(llm_config), registry, executor, context)
    memory = MemoryStore(memory_path or "~/.deskagent/memory.sqlite")
    return runtime.create_agent(
        allowed_actions, max_iterations, create_checkpointer(checkpoint_path),
        ActionPolicy(policy_config), ToolRouter(), Telemetry(telemetry_path),
        memory, screen_provider, EventBus(), ProactiveRules(), SkillStore(registry, skills_path),
    )
