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


class Collect(Action):
    name = "collect"
    description = "Collect structured input"
    category = ActionCategory.PRODUCTIVITY
    parameters_schema = {
        "items": {"type": "list", "required": True},
        "options": {"type": "dict", "required": True},
    }

    def execute(self, context, parameters):
        context.structured = parameters
        return ActionResult(True, parameters)


class UseSecret(Action):
    name = "use_secret"
    description = "Use a secret reference"
    category = ActionCategory.PRODUCTIVITY
    parameters_schema = {"token": {"type": "string", "required": True}}

    def execute(self, context, parameters):
        context.secret = parameters["token"]
        return ActionResult(True)


@pytest.fixture
def workflow_runtime(tmp_path):
    registry = ActionRegistry()
    registry.register(Record)
    registry.register(Collect)
    registry.register(UseSecret)
    context = SimpleNamespace(
        logger=logging.getLogger("workflow-test"), values=[], structured=None, secret=None,
    )
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


def test_workflow_lifecycle_and_schema_migration(workflow_runtime):
    workflows, _, _ = workflow_runtime
    saved = workflows.save({
        "schema_version": 1,
        "name": "lifecycle",
        "steps": [{"id": "record", "title": "Record", "tool": "record", "arguments": {"value": 1}}],
    })
    assert saved["schema_version"] == 2
    updated = workflows.update("lifecycle", saved)
    assert updated["version"] == 2
    exported = workflows.export_yaml("lifecycle")
    assert "name: lifecycle" in exported
    workflows.disable("lifecycle")
    with pytest.raises(KeyError):
        workflows.get("lifecycle")
    workflows.enable("lifecycle")
    workflows.archive("lifecycle")
    assert workflows.list() == []
    assert workflows.list(detailed=True) == []
    workflows.delete("lifecycle")


def test_structured_and_secret_inputs_are_supported(workflow_runtime, monkeypatch):
    workflows, engine, context = workflow_runtime
    workflows.save({
        "name": "structured",
        "inputs": {
            "items": {"type": "list", "required": True},
            "options": {"type": "dict", "required": True},
        },
        "steps": [{
            "id": "collect", "title": "Collect", "action": "collect",
            "arguments": {"items": "${inputs.items}", "options": "${inputs.options}"},
        }],
    })
    result = workflows.run(engine, "structured", {"items": [1, 2], "options": {"safe": True}})
    assert result.status is SessionStatus.COMPLETED
    assert context.structured == {"items": [1, 2], "options": {"safe": True}}

    monkeypatch.setenv("DESKAGENT_SECRET_API_TOKEN", "raw-secret")
    workflows.save({
        "name": "secret",
        "inputs": {"token_ref": {"type": "string", "required": True, "secret": True}},
        "steps": [{
            "id": "secret", "title": "Secret", "action": "use_secret",
            "arguments": {"token": "${inputs.token_ref}"},
        }],
    })
    session = workflows.run(engine, "secret", {"token_ref": "api_token"})
    assert session.status is SessionStatus.COMPLETED
    assert context.secret == "raw-secret"
    assert session.plan.metadata["inputs"]["token_ref"] == "***SECRET_REF***"
