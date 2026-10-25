import logging

from deskagent.actions.executor import ActionExecutor
from deskagent.agent.llm.config import LLMConfig
from deskagent.agent.llm.factory import create_llm
from deskagent.agent.runtime import AgentRuntime
from deskagent.agent.tools import create_mvp_action_registry
from deskagent.core.config import Settings
from deskagent.core.context import ActionContext
from deskagent.core.services import ServicesFactory


def create_desktop_agent(
    llm_config: LLMConfig | None = None,
    allowed_actions=None,
    max_iterations=6,
    confirmation_handler=None,
):
    registry = create_mvp_action_registry()
    context = ActionContext(
        settings=Settings(),
        logger=logging.getLogger("deskagent"),
        services=ServicesFactory.create(),
    )
    executor = ActionExecutor(
        registry=registry,
        confirmation_handler=confirmation_handler,
    )
    runtime = AgentRuntime(
        llm=create_llm(llm_config),
        registry=registry,
        executor=executor,
        context=context,
    )
    return runtime.create_agent(
        allowed_actions=allowed_actions,
        max_iterations=max_iterations,
    )
