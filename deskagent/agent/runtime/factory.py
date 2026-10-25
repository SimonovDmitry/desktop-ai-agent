import logging
from dataclasses import dataclass

from deskagent.actions.base import ActionRegistry
from deskagent.actions.contracts import ActionContractValidator
from deskagent.actions.executor import ActionExecutor
from deskagent.actions.registry import create_action_registry
from deskagent.agent.agent import DesktopAgent
from deskagent.agent.capabilities.events import EventBus, ProactiveRules
from deskagent.agent.capabilities.memory import MemoryStore
from deskagent.agent.capabilities.perception import ContextCollector
from deskagent.agent.capabilities.policy import ActionPolicy, PolicyConfig
from deskagent.agent.capabilities.routing import ToolRouter
from deskagent.agent.capabilities.skills import SkillStore
from deskagent.agent.capabilities.telemetry import Telemetry
from deskagent.agent.capabilities.tools import ActionToolCatalog
from deskagent.agent.core.graph import AgentGraph
from deskagent.agent.llm.base import LLMProvider
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.factory import create_llm
from deskagent.agent.runtime.checkpoints import create_checkpointer
from deskagent.core.config import Settings
from deskagent.core.context import ActionContext
from deskagent.core.permissions import PermissionManager
from deskagent.core.services import ServicesFactory
from deskagent.safety.audit import AuditLog
from deskagent.safety.limits import SafetyLimits


@dataclass
class AgentRuntime:
    llm: LLMProvider
    registry: ActionRegistry
    executor: ActionExecutor
    context: object

    def create_agent(self, allowed_actions=None, max_iterations=8, max_tool_calls=6,
                     checkpointer=None, policy=None, router=None, telemetry=None, memory=None, screen_provider=None,
                     event_bus=None, proactive_rules=None, skills=None, audit_log=None, limits=None):
        tools = ActionToolCatalog(
            self.registry, self.executor, self.context, allowed_actions, policy,
            audit_log=audit_log, limits=limits,
        )
        graph = AgentGraph(self.llm, tools, max_iterations, max_tool_calls, checkpointer=checkpointer,
                           router=router, telemetry=telemetry)
        return DesktopAgent(
            graph, context_collector=ContextCollector(self.context, screen_provider), memory=memory,
            event_bus=event_bus, proactive_rules=proactive_rules, skills=skills,
        )


def create_desktop_agent(llm_config: LLMConfig, allowed_actions=None, max_iterations=None,
                         checkpoint_path=None, memory_path=None, telemetry_path=None,
                         policy_config: PolicyConfig | None = None, registry=None, screen_provider=None,
                         skills_path=None, settings: Settings | None = None, config_path=None):
    settings = settings or Settings.load(config_path)
    context = ActionContext(settings, logging.getLogger("deskagent"), ServicesFactory.create())
    registry = registry or create_action_registry(context=context)
    ActionContractValidator(context).validate_registry(registry)
    permissions = PermissionManager()
    executor = ActionExecutor(registry, permission_checker=permissions, confirmation_handler=lambda *_: True)
    runtime = AgentRuntime(create_llm(llm_config), registry, executor, context)
    security = settings.security
    policy_config = policy_config or PolicyConfig(
        dry_run=security.dry_run, max_actions=security.max_actions, allow_shell=security.allow_shell,
        strict_mode=security.strict_mode, confirm_medium=security.confirm_medium,
        shell_allowed_commands=tuple(security.shell_allowed_commands),
        allowed_paths=tuple(security.allowed_paths), blocked_paths=tuple(security.blocked_paths),
        allowed_applications=tuple(security.allowed_applications),
    )
    memory = MemoryStore(memory_path or settings.storage.memory)
    return runtime.create_agent(
        allowed_actions, max_iterations or settings.agent.max_iterations,
        settings.agent.max_tool_calls_per_iteration, create_checkpointer(checkpoint_path or settings.storage.checkpoints),
        ActionPolicy(policy_config), ToolRouter(settings.agent.max_tools),
        Telemetry(telemetry_path or settings.storage.telemetry), memory, screen_provider,
        EventBus(), ProactiveRules(), SkillStore(registry, skills_path or settings.storage.skills),
        AuditLog(settings.storage.audit),
        SafetyLimits(security.max_clicks_per_minute, security.max_consecutive_failures),
    )
