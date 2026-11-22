"""Read-only inspection of versioned declarative workflows."""
from __future__ import annotations

import json
from collections import Counter

from deskagent.actions.productivity._common import (
    MAX_ITEMS, NAME, ProductivityAction, query_rows, with_store,
)
from deskagent.actions.registry import create_action_registry
from deskagent.autopilot.validation import PlanValidator
from deskagent.autopilot.workflows import WorkflowRegistry
from deskagent.privacy.confirmation import redact


def _definition(context, name):
    records = query_rows(context,
                         "SELECT definition_json FROM workflows WHERE name=? AND archived=0 "
                         "ORDER BY version DESC LIMIT 1", (name,))
    if not records:
        raise KeyError(name)
    return json.loads(records[0]["definition_json"])


def _registry(store):
    catalog = create_action_registry(include_plugins=False)
    return WorkflowRegistry(store, PlanValidator(catalog))


class ListTaskWorkflows(ProductivityAction):
    name = "list_task_workflows"
    description = "List saved workflow names, versions and enabled states"
    parameters_schema = {}
    discoverable = True

    def execute(self, context, parameters):
        def operation(store):
            workflows = store.list_workflows()
            return {"workflows": workflows[:200], "total": len(workflows),
                    "truncated": len(workflows) > 200}
        return self.run(lambda: with_store(context, operation))


class GetTaskWorkflowDefinition(ProductivityAction):
    name = "get_task_workflow_definition"
    description = "Read a bounded redacted workflow definition"
    parameters_schema = NAME
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            definition = _definition(context, parameters["name"])
            return {"name": parameters["name"], "version": definition.get("version", 1),
                    "title": definition.get("title"), "description": definition.get("description"),
                    "steps": redact(definition.get("steps", []))[:100],
                    "truncated": len(definition.get("steps", [])) > 100}
        return self.run(operation)


class GetTaskWorkflowInputs(ProductivityAction):
    name = "get_task_workflow_inputs"
    description = "Read workflow input names, types and required flags"
    parameters_schema = NAME
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            definition = _definition(context, parameters["name"])
            inputs = definition.get("inputs", {})
            return {"name": parameters["name"], "inputs": [
                {"name": name, "type": schema.get("type", "string"),
                 "required": schema.get("required", False),
                 "secret": schema.get("secret", False),
                 "has_default": "default" in schema}
                for name, schema in list(inputs.items())[:100]
            ], "truncated": len(inputs) > 100}
        return self.run(operation)


class GetTaskWorkflowSchedule(ProductivityAction):
    name = "get_task_workflow_schedule"
    description = "Read declared workflow schedule and next run time"
    parameters_schema = NAME
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            definition = _definition(context, parameters["name"])
            return {"name": parameters["name"], "schedule": definition.get("schedule"),
                    "has_schedule": bool(definition.get("schedule"))}
        return self.run(operation)


class GetTaskWorkflowRuns(ProductivityAction):
    name = "get_task_workflow_runs"
    description = "List bounded workflow run statuses without input values"
    parameters_schema = NAME
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            name = parameters["name"]
            _definition(context, name)
            items = query_rows(context,
                               "SELECT id, version, session_id, status, started_at, finished_at "
                               "FROM workflow_runs WHERE name=? ORDER BY id DESC LIMIT 501", (name,))
            return {"name": name, "runs": items[:MAX_ITEMS], "truncated": len(items) > MAX_ITEMS}
        return self.run(operation)


class GetTaskWorkflowVersions(ProductivityAction):
    name = "get_task_workflow_versions"
    description = "List versions and timestamps for a saved workflow"
    parameters_schema = NAME
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            name = parameters["name"]
            _definition(context, name)
            items = query_rows(context,
                               "SELECT version, created_at, enabled, archived FROM workflows "
                               "WHERE name=? ORDER BY version DESC LIMIT 501", (name,))
            return {"name": name, "versions": items[:MAX_ITEMS], "truncated": len(items) > MAX_ITEMS}
        return self.run(operation)


class GetTaskWorkflowPermissions(ProductivityAction):
    name = "get_task_workflow_permissions"
    description = "Read workflow-level permission declarations"
    parameters_schema = NAME
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            definition = _definition(context, parameters["name"])
            return {"name": parameters["name"],
                    "required_permissions": definition.get("required_permissions", [])[:100]}
        return self.run(operation)


class GetTaskWorkflowActionUsage(ProductivityAction):
    name = "get_task_workflow_action_usage"
    description = "Count actions referenced by a workflow definition"
    parameters_schema = NAME
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            definition = _definition(context, parameters["name"])
            counts = Counter(step.get("action") for step in definition.get("steps", []))
            return {"name": parameters["name"], "actions": [
                {"action": action, "steps": count} for action, count in counts.most_common(100)
            ], "truncated": len(counts) > 100}
        return self.run(operation)


class ValidateTaskWorkflowInputs(ProductivityAction):
    name = "validate_task_workflow_inputs"
    description = "Validate workflow inputs and plan without starting a run"
    parameters_schema = {**NAME, "inputs": {"type": "dict", "required": False}}
    discoverable = True

    def execute(self, context, parameters):
        def operation(store):
            workflow = _registry(store)
            definition = _definition(context, parameters["name"])
            plan = workflow.instantiate(definition, parameters.get("inputs", {}))
            return {"name": parameters["name"], "valid": True,
                    "plan_steps": len(plan.steps), "plan_version": plan.version}
        return self.run(lambda: with_store(context, operation))


class PreviewTaskWorkflowPlan(ProductivityAction):
    name = "preview_task_workflow_plan"
    description = "Preview a validated workflow's rendered steps without executing"
    parameters_schema = {**NAME, "inputs": {"type": "dict", "required": False}}
    discoverable = True

    def execute(self, context, parameters):
        def operation(store):
            workflow = _registry(store)
            definition = _definition(context, parameters["name"])
            plan = workflow.instantiate(definition, parameters.get("inputs", {}))
            return {"name": parameters["name"], "steps": [
                {"id": step.id, "title": step.title, "action": step.action,
                 "arguments": redact(step.arguments), "depends_on": list(step.depends_on)}
                for step in plan.steps[:100]
            ], "truncated": len(plan.steps) > 100}
        return self.run(lambda: with_store(context, operation))
