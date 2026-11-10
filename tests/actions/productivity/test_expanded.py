from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from deskagent.actions.productivity import plan_inspection as plans
from deskagent.actions.productivity import session_inspection as sessions
from deskagent.actions.productivity import workflow_inspection as workflows
from deskagent.actions.registry import create_action_registry
from deskagent.autopilot.models import Plan, Session, SessionStatus, Step, StepStatus
from deskagent.autopilot.store import SessionStore
from deskagent.core.config import Settings, StorageSettings


def context(tmp_path):
    return SimpleNamespace(settings=Settings(
        storage=StorageSettings(autopilot=str(tmp_path / "autopilot.sqlite"))
    ))


def populate(tmp_path):
    store = SessionStore(tmp_path / "autopilot.sqlite")
    first = Step("a", "First", "get_task_progress", {"session_id": "x"})
    first.status = StepStatus.SUCCEEDED
    first.attempts = 1
    first.output = {"password": "secret", "value": 7}
    second = Step("b", "Second", "get_task_progress", {"session_id": "x"}, depends_on=("a",))
    second.status = StepStatus.BLOCKED
    third = Step("c", "Third", "get_task_progress", {"session_id": "x"}, depends_on=("b",))
    third.status = StepStatus.RETRY_SCHEDULED
    third.attempts = 1
    third.retry_at = (datetime.now(UTC) + timedelta(minutes=1)).isoformat()
    session = Session("Prepare report", Plan([first, second, third]),
                      status=SessionStatus.RUNNING, current_step_id="b",
                      started_at=(datetime.now(UTC) - timedelta(minutes=2)).isoformat())
    store.create(session)
    store.save(session, event="step_succeeded", step_id="a", payload={"token": "hidden"})
    store.begin_attempt(session.id, "a", 1)
    store.finish_attempt(session.id, "a", 1, "succeeded")
    store.add_verification(session.id, "a", 1, "catalog", True, {"token": "hidden"})
    store.put_approval("approval-1", session.id, "b", 1, "hash", {"question": "Approve?"})
    store.start_tool_call("call-1", session.id, "a", 1, "get_task_progress",
                          {"session_id": "x"}, None)
    store.finish_tool_call("call-1", "succeeded", {"success": True})
    store.add_artifact(session.id, "report", "file:///tmp/report.txt", "a", {"secret": "hidden"})
    other = Session("Other task", Plan([Step("x", "Other", "get_task_progress", {"session_id": "x"})]),
                    status=SessionStatus.COMPLETED)
    store.create(other)
    definition = {
        "name": "demo", "version": 1, "title": "Demo",
        "required_permissions": ["screen_recording"],
        "inputs": {"label": {"type": "string", "required": True}},
        "steps": [{"id": "one", "title": "One", "action": "get_task_progress",
                   "arguments": {"session_id": "$" + "{inputs.label}"}}],
        "schedule": {"interval_seconds": 3600, "next_run_at": "2099-01-01T00:00:00+00:00"},
    }
    store.put_workflow("demo", 1, definition)
    store.start_workflow_run("demo", 1, session.id, {"label": "secret"})
    store.close()
    return session.id, other.id


def test_session_inspection_actions(tmp_path):
    session_id, other_id = populate(tmp_path)
    ctx = context(tmp_path)
    base = {"session_id": session_id}
    actions = [
        (sessions.ListTaskSessions(), {}),
        (sessions.GetTaskSummary(), base),
        (sessions.GetTaskStepDetail(), {**base, "step_id": "a"}),
        (sessions.GetTaskStepOutput(), {**base, "step_id": "a"}),
        (sessions.ListTaskEvents(), base),
        (sessions.GetTaskBlockers(), base),
        (sessions.GetTaskReadySteps(), base),
        (sessions.GetTaskRetrySchedule(), base),
        (sessions.GetTaskDependencyGraph(), base),
        (sessions.GetTaskTimeline(), base),
        (sessions.GetTaskArtifacts(), base),
        (sessions.GetTaskAttempts(), base),
        (sessions.GetTaskVerifications(), base),
        (sessions.GetTaskApprovals(), base),
        (sessions.GetTaskToolCalls(), base),
        (sessions.GetTaskStoreMetrics(), {}),
        (sessions.GetTaskDuration(), base),
        (sessions.CompareTaskSessions(), {"first_session_id": session_id,
                                          "second_session_id": other_id}),
        (sessions.GetTaskActionUsage(), base),
        (sessions.GetTaskCompletionEvidence(), base),
    ]
    results = {}
    for action, parameters in actions:
        result = action.execute(ctx, parameters)
        assert result.success, (action.name, result.error)
        results[action.name] = result.data
    assert results["get_task_summary"]["completed_steps"] == 1
    assert "secret" not in results["get_task_step_output"]["output_json"]
    assert "REDACTED" in results["get_task_step_output"]["output_json"]
    assert results["get_task_blockers"]["blockers"][0]["step_id"] == "c"
    assert results["get_task_ready_steps"]["steps"][0]["step_id"] == "b"
    assert results["get_task_attempts"]["attempts"][0]["status"] == "succeeded"
    assert results["get_task_verifications"]["verifications"][0]["success"] == 1
    assert results["get_task_approvals"]["approvals"][0]["status"] == "pending"
    assert results["get_task_tool_calls"]["tool_calls"][0]["action"] == "get_task_progress"
    assert results["get_task_completion_evidence"]["successful_steps"][0]["verified_checks"] == 1


def test_workflow_inspection_actions(tmp_path):
    populate(tmp_path)
    ctx = context(tmp_path)
    base = {"name": "demo"}
    actions = [
        (workflows.ListTaskWorkflows(), {}),
        (workflows.GetTaskWorkflowDefinition(), base),
        (workflows.GetTaskWorkflowInputs(), base),
        (workflows.GetTaskWorkflowSchedule(), base),
        (workflows.GetTaskWorkflowRuns(), base),
        (workflows.GetTaskWorkflowVersions(), base),
        (workflows.GetTaskWorkflowPermissions(), base),
        (workflows.GetTaskWorkflowActionUsage(), base),
        (workflows.ValidateTaskWorkflowInputs(), {**base, "inputs": {"label": "x"}}),
        (workflows.PreviewTaskWorkflowPlan(), {**base, "inputs": {"label": "x"}}),
    ]
    results = {}
    for action, parameters in actions:
        result = action.execute(ctx, parameters)
        assert result.success, (action.name, result.error)
        results[action.name] = result.data
    assert results["list_task_workflows"]["total"] == 1
    assert results["get_task_workflow_runs"]["runs"][0]["status"] == "running"
    assert results["get_task_workflow_inputs"]["inputs"][0]["required"]
    assert results["preview_task_workflow_plan"]["steps"][0]["arguments"]["session_id"] == "x"
    assert not workflows.ValidateTaskWorkflowInputs().execute(ctx, base).success
    store = SessionStore(tmp_path / "autopilot.sqlite")
    store.set_workflow_state("demo", enabled=False)
    store.close()
    assert workflows.GetTaskWorkflowDefinition().execute(ctx, base).success
    assert workflows.PreviewTaskWorkflowPlan().execute(
        ctx, {**base, "inputs": {"label": "x"}}
    ).success


def plan():
    return Plan([
        Step("a", "Start", "get_task_progress", {"session_id": "x"}, timeout_seconds=1),
        Step("b", "Continue", "get_task_progress", {"session_id": "x"},
             depends_on=("a",), timeout_seconds=5),
        Step("c", "Tests", "run_project_tests", {"directory": "/tmp"},
             depends_on=("a",), timeout_seconds=2),
    ]).to_dict()


def test_plan_analysis_actions():
    value = plan()
    actions = [
        (plans.ValidateTaskPlan(), {"plan": value}),
        (plans.GetPlanDependencyOrder(), {"plan": value}),
        (plans.GetPlanParallelGroups(), {"plan": value}),
        (plans.GetPlanCriticalPathEstimate(), {"plan": value}),
        (plans.GetPlanRiskSummary(), {"plan": value}),
        (plans.GetPlanActionUsage(), {"plan": value}),
        (plans.GetPlanRetryBudget(), {"plan": value}),
        (plans.GetPlanConfirmationSteps(), {"plan": value}),
        (plans.GetPlanVerificationCoverage(), {"plan": value}),
        (plans.CompareTaskPlans(), {"first_plan": value, "second_plan": value}),
    ]
    results = {}
    for action, parameters in actions:
        result = action.execute(None, parameters)
        assert result.success, (action.name, result.error)
        results[action.name] = result.data
    assert results["validate_task_plan"]["valid"]
    assert results["get_plan_dependency_order"]["groups"] == [["a"], ["b", "c"]]
    assert results["get_plan_parallel_groups"]["groups"][1]["shared_resources"] == ["desktop_ui"]
    assert results["get_plan_critical_path_estimate"]["critical_step_ids"] == ["a", "b"]
    assert results["get_plan_confirmation_steps"]["steps"][0]["step_id"] == "c"
    assert results["compare_task_plans"]["unchanged"] == 3
    invalid = plan()
    invalid["steps"][1]["depends_on"] = ["missing"]
    assert not plans.ValidateTaskPlan().execute(None, {"plan": invalid}).data["valid"]


def test_productivity_actions_are_registered():
    registry = create_action_registry(include_plugins=False)
    for name in ("list_task_sessions", "get_task_verifications", "get_task_workflow_runs",
                 "validate_task_plan", "get_plan_critical_path_estimate"):
        assert registry.contains(name)
