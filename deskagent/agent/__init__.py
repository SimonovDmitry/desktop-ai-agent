import sys
from importlib import import_module

from deskagent.agent.agent import DesktopAgent
from deskagent.agent.capabilities.memory import MemoryStore
from deskagent.agent.capabilities.policy import ActionPolicy, PolicyConfig
from deskagent.agent.core.models import ActionExecution, AgentResponse, AgentSession, PlanStep
from deskagent.agent.runtime.factory import AgentRuntime, create_desktop_agent

_COMPAT_MODULES = {
    "checkpoints": "runtime.checkpoints", "factory": "runtime.factory",
    "graph": "core.graph", "models": "core.models", "prompts": "core.prompts", "state": "core.state",
    "events": "capabilities.events", "memory": "capabilities.memory",
    "perception": "capabilities.perception", "policy": "capabilities.policy",
    "routing": "capabilities.routing", "skills": "capabilities.skills",
    "telemetry": "capabilities.telemetry", "tools": "capabilities.tools",
}
for _name, _target in _COMPAT_MODULES.items():
    sys.modules.setdefault(f"{__name__}.{_name}", import_module(f"{__name__}.{_target}"))
del _name, _target

__all__ = [
    "ActionExecution", "ActionPolicy", "AgentResponse", "AgentRuntime", "AgentSession",
    "DesktopAgent", "MemoryStore", "PlanStep", "PolicyConfig", "create_desktop_agent",
]
