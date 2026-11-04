from __future__ import annotations

import json
import re
from typing import Protocol

from deskagent.autopilot.models import Plan


class PlanService(Protocol):
    def create_plan(self, goal: str, tools: list[dict]) -> Plan:
        ...

    def replan(self, session, failed_step, error: str, tools: list[dict]) -> Plan:
        ...


class LLMPlanService:
    """Use an LLM for plan proposals; the deterministic engine remains authoritative."""

    def __init__(self, llm):
        self.llm = llm

    def create_plan(self, goal: str, tools: list[dict]) -> Plan:
        return self._generate(
            "Create a safe deterministic execution plan for the user goal.",
            {"goal": goal, "available_tools": tools},
        )

    def replan(self, session, failed_step, error: str, tools: list[dict]) -> Plan:
        return self._generate(
            "Revise only the unfinished portion of this plan after a failure. "
            "Keep completed step ids and actions unchanged.",
            {
                "goal": session.goal,
                "plan": session.plan.to_dict(),
                "failed_step": failed_step.to_dict(),
                "error": error,
                "available_tools": tools,
            },
        )

    def _generate(self, instruction: str, context: dict) -> Plan:
        schema = {
            "version": 1,
            "steps": [{
                "id": "stable_id", "title": "Human readable title",
                "action": "tool_name", "arguments": {}, "depends_on": [],
                "idempotent": False,
            }],
        }
        prompt = (
            f"{instruction}\nReturn JSON only. Do not include prose or executable code.\n"
            f"Required shape: {json.dumps(schema)}\nContext: "
            f"{json.dumps(context, ensure_ascii=False, default=str)}"
        )
        response = self.llm.generate([{"role": "user", "content": prompt}])
        text = str(response.content).strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
        if fenced:
            text = fenced.group(1)
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("Planner returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("Planner response must be an object")
        return Plan.from_dict(value)
