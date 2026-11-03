import logging
from types import SimpleNamespace

import pytest

from deskagent.actions.base import Action, ActionRegistry
from deskagent.actions.executor import ActionExecutor
from deskagent.actions.types import ActionCategory, ActionResult
from deskagent.agent.capabilities.tools import ActionToolCatalog
from deskagent.autopilot import AutopilotEngine, PlanValidator, SessionStatus, SessionStore, WorkflowRegistry
from deskagent.autopilot.workflows import WorkflowValidationError


class Record(Action):
    name = "record"
    description = "Record a value"
    category = ActionCategory.PRODUCTIVITY
    parameters_schema = {"value": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        context.values.append(parameters["value"])
        return ActionResult(True, parameters)


@pytest.fixture
def workflow_runtime(tmp_path):
    registry = ActionRegistry()
    registry.register(Record)
    context = SimpleNamespace(logger=logging.getLogger("workflow-test"), values=[])
    catalog = ActionToolCatalog(registry, ActionExecutor(registry), context)
    store = SessionStore(tmp_path / "workflow.sqlite")
    engine = AutopilotEngine(catalog, store, sleep=lambda _: None)
    workflows = WorkflowRegistry(store, PlanValidator(registry))
    yield workflows, engine, context
    store.close()


def test_versioned_yaml_workflow_is_instantiated_and_run(workflow_runtime):
    workflows, engine, context = workflow_runtime
    workflows.save(
        """
name: morning
version: 1
inputs:
  volume:
    type: integer
    required: true
    minimum: 0
    maximum: 100
steps:
  - id: configure
    title: Configure
    action: record
    arguments:
      value: ${inputs.volume}
"""
    )

    result = workflows.run(engine, "morning", {"volume": 25})

    assert result.status is SessionStatus.COMPLETED
    assert context.values == [25]
    assert workflows.list() == [{"name": "morning", "version": 1}]


def test_workflow_validates_required_and_unknown_inputs(workflow_runtime):
    workflows, _, _ = workflow_runtime
    definition = workflows.save(
        {
            "name": "typed",
            "inputs": {"count": {"type": "integer", "required": True}},
            "steps": [{"id": "record", "title": "Record", "action": "record", "arguments": {"value": 1}}],
        }
    )
    with pytest.raises(WorkflowValidationError, match="Missing required"):
        workflows.instantiate(definition, {})
    with pytest.raises(WorkflowValidationError, match="Unknown inputs"):
        workflows.instantiate(definition, {"count": 1, "extra": True})
