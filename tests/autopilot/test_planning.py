import json

import pytest

from deskagent.agent.llm.response import LLMResponse
from deskagent.autopilot.planning import LLMPlanService


class FakeLLM:
    def __init__(self, content):
        self.content = content
        self.messages = None

    def generate(self, messages, tools=None):
        self.messages = messages
        return LLMResponse(content=self.content)


def test_llm_plan_service_parses_structured_plan():
    value = {
        "version": 1,
        "steps": [{"id": "one", "title": "One", "action": "count", "arguments": {}}],
    }
    llm = FakeLLM(f"```json\n{json.dumps(value)}\n```")
    plan = LLMPlanService(llm).create_plan("do it", [])
    assert plan.step("one").action == "count"
    assert "Return JSON only" in llm.messages[0]["content"]


def test_llm_plan_service_rejects_non_json():
    with pytest.raises(ValueError, match="invalid JSON"):
        LLMPlanService(FakeLLM("I think you should click it")).create_plan("do it", [])
