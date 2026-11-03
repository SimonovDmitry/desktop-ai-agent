import logging
from types import SimpleNamespace

from deskagent.agent.graph import AgentGraph
from deskagent.agent.models import AgentSession
from deskagent.agent.tools import ActionToolCatalog

from deskagent.actions.base import Action, ActionRegistry
from deskagent.actions.executor import ActionExecutor
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel
from deskagent.agent.agent import DesktopAgent
from deskagent.agent.llm.base import LLMProvider
from deskagent.agent.llm.response import LLMResponse, ToolCall


class EchoAction(Action):
    name = "echo"
    description = "Return the provided text"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.NONE
    parameters_schema = {
        "text": {
            "type": "string",
            "required": True,
            "description": "Text to return",
        }
    }

    def execute(self, context, parameters):
        return ActionResult(
            success=True,
            data={"text": parameters["text"]},
        )


class FakeLLM(LLMProvider):
    def __init__(self):
        self.calls = 0

    def generate(self, messages, tools=None):
        self.calls += 1
        if self.calls % 2 == 1:
            return LLMResponse(
                tool_calls=[
                    ToolCall(
                        id="call_echo",
                        name="echo",
                        arguments={"text": "hello"},
                    )
                ]
            )
        return LLMResponse(content="Готово: hello")


def create_agent():
    registry = ActionRegistry()
    registry.register(EchoAction)
    executor = ActionExecutor(registry)
    context = SimpleNamespace(logger=logging.getLogger("test-agent"))
    tools = ActionToolCatalog(
        registry=registry,
        executor=executor,
        context=context,
        allowed_names=["echo"],
    )
    llm = FakeLLM()
    graph = AgentGraph(llm=llm, tools=tools)
    return DesktopAgent(graph), llm, tools


def test_agent_executes_tool_and_returns_final_response():
    agent, llm, _ = create_agent()

    response = agent.ask(
        "Повтори hello",
        session=AgentSession(thread_id="test-thread"),
    )

    assert response.content == "Готово: hello"
    assert response.error is None
    assert llm.calls == 2
    assert len(response.actions) == 1
    assert response.actions[0].name == "echo"
    assert response.actions[0].success is True
    assert response.actions[0].data == {"text": "hello"}


def test_tool_schema_contains_required_parameters():
    _, _, tools = create_agent()

    schema = tools.schemas()[0]["function"]

    assert schema["name"] == "echo"
    assert schema["parameters"]["required"] == ["text"]
    assert schema["parameters"]["properties"]["text"] == {
        "type": "string",
        "description": "Text to return",
    }


def test_session_response_contains_only_current_action_executions():
    agent, _, _ = create_agent()
    session = AgentSession(thread_id="reused-thread")

    first = agent.ask("Повтори hello", session=session)
    second = agent.ask("Повтори ещё раз", session=session)

    assert len(first.actions) == 1
    assert len(second.actions) == 1
    assert second.actions[0].tool_call_id == "call_echo"
