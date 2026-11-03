import logging
from types import SimpleNamespace

from deskagent.agent.checkpoints import create_checkpointer
from deskagent.agent.graph import AgentGraph
from deskagent.agent.memory import MemoryStore
from deskagent.agent.models import AgentSession
from deskagent.agent.policy import ActionPolicy, PolicyConfig
from deskagent.agent.prompts import build_system_prompt
from deskagent.agent.routing import ToolRouter
from deskagent.agent.skills import SkillStore
from deskagent.agent.tools import ActionToolCatalog

from deskagent.actions.base import Action, ActionRegistry
from deskagent.actions.executor import ActionExecutor
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel
from deskagent.agent.agent import DesktopAgent
from deskagent.agent.llm.base import LLMProvider, LLMProviderError
from deskagent.agent.llm.response import LLMResponse, ToolCall
from deskagent.agent.llm.router import FallbackLLM


class DangerousAction(Action):
    name = "dangerous_action"
    description = "Perform a dangerous operation"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    parameters_schema = {}

    def execute(self, context, parameters):
        context.executions += 1
        return ActionResult(True, {"executed": True})


class ConfirmationLLM(LLMProvider):
    def generate(self, messages, tools=None):
        has_result = any(getattr(message, "type", None) == "tool" for message in messages)
        if has_result:
            return LLMResponse(content="Выполнено")
        return LLMResponse(tool_calls=[ToolCall("dangerous_action", {}, "danger-call")])


def create_dangerous_agent(path, context):
    registry = ActionRegistry()
    registry.register(DangerousAction)
    executor = ActionExecutor(registry, confirmation_handler=lambda *_: True)
    tools = ActionToolCatalog(registry, executor, context, ["dangerous_action"])
    graph = AgentGraph(ConfirmationLLM(), tools, checkpointer=create_checkpointer(path))
    return DesktopAgent(graph)


def test_interrupt_is_persisted_and_resumed(tmp_path):
    path = tmp_path / "checkpoints.sqlite"
    context = SimpleNamespace(logger=logging.getLogger("test"), executions=0)
    session = AgentSession("persistent-thread")

    response = create_dangerous_agent(path, context).ask("Сделай опасное действие", session)
    assert response.interrupted is True
    assert context.executions == 0

    response = create_dangerous_agent(path, context).confirm(session.thread_id, True)
    assert response.content == "Выполнено"
    assert context.executions == 1
    assert response.actions[0].verified is True


def test_denied_action_is_not_executed(tmp_path):
    context = SimpleNamespace(logger=logging.getLogger("test"), executions=0)
    agent = create_dangerous_agent(tmp_path / "deny.sqlite", context)
    response = agent.ask("Сделай опасное действие", AgentSession("deny-thread"))

    response = agent.confirm(response.thread_id, False)

    assert context.executions == 0
    assert response.actions[0].error_code == "ACTION_CANCELLED"


def test_stream_contains_action_and_completion_events():
    from tests.agent.test_agent import create_agent

    agent, _, _ = create_agent()
    events = list(agent.stream_ask("Повтори hello", AgentSession("stream-thread")))
    names = [event["event"] for event in events]

    assert "action_started" in names
    assert "action_finished" in names
    assert "token" in names
    assert names[-1] == "done"


def test_policy_blocks_sensitive_paths():
    policy = ActionPolicy(PolicyConfig(blocked_paths=("/secret",)))
    decision = policy.evaluate(DangerousAction, {"path": "/secret/key"})
    assert decision.allowed is False


def test_policy_blocks_shell_and_unknown_applications():
    class ShellAction(DangerousAction):
        name = "run_command"

    class LaunchAction(DangerousAction):
        name = "launch_application"

    policy = ActionPolicy(PolicyConfig(allowed_applications=("PyCharm",)))
    assert policy.evaluate(ShellAction, {"command": "echo hi"}).allowed is False
    assert policy.evaluate(LaunchAction, {"application": "Safari"}).allowed is False


def test_policy_confirms_overwrites():
    class WriteAction(DangerousAction):
        name = "write_file"
        risk_level = RiskLevel.MEDIUM
        requires_confirmation = False

    policy = ActionPolicy()
    assert policy.evaluate(WriteAction, {"path": "/tmp/a", "overwrite": True}).confirmation_required
    assert not policy.evaluate(WriteAction, {"path": "/tmp/a", "overwrite": False}).confirmation_required


def test_catalog_uses_full_registry_by_default():
    registry = ActionRegistry()
    registry.register(DangerousAction)
    catalog = ActionToolCatalog(registry, None, None)
    assert catalog.allowed_names == ("dangerous_action",)


def test_router_limits_tools():
    registry = ActionRegistry()
    registry.register(DangerousAction)
    selected = ToolRouter(max_tools=1).select("system operation", registry)
    assert selected == ["dangerous_action"]


def test_router_prioritizes_requested_intent():
    class LaunchAction(DangerousAction):
        name = "launch_application"
        description = "Launch an application"

    registry = ActionRegistry()
    registry.register(DangerousAction)
    registry.register(LaunchAction)
    selected = ToolRouter(max_tools=1).select("Открой приложение", registry)
    assert selected == ["launch_application"]


def test_prompt_contains_dynamic_context():
    prompt = build_system_prompt(
        {"application": "Safari"},
        {"battery": {"percentage": 9}, "focus_mode": True, "procrastination": True},
    )
    assert "Safari" in prompt
    assert "percentage" in prompt
    assert "Epictetus" in prompt


def test_memory_indexes_and_finds_documents(tmp_path):
    memory = MemoryStore(tmp_path / "memory.sqlite")
    memory.index_text("notes.txt", "A local desktop agent can use tools safely.")
    results = memory.search("desktop agent", "documents")
    assert results[0]["value"]["source"] == "notes.txt"


def test_skills_are_disabled_until_approved(tmp_path):
    registry = ActionRegistry()
    registry.register(DangerousAction)
    skills = SkillStore(registry, tmp_path / "skills")
    slug = skills.save("Danger demo", [{"action": "dangerous_action", "parameters": {}}])
    assert skills.load(slug)["enabled"] is False
    skills.enable(slug)
    assert skills.load(slug)["enabled"] is True


def test_llm_fallback_uses_next_provider():
    class BrokenLLM(LLMProvider):
        def generate(self, messages, tools=None):
            raise LLMProviderError("offline")

    class WorkingLLM(LLMProvider):
        def generate(self, messages, tools=None):
            return LLMResponse(content="ok")

    response = FallbackLLM([BrokenLLM(), WorkingLLM()]).generate([])
    assert response.content == "ok"
