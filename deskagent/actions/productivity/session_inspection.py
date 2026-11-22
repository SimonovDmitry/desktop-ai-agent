"""Read-only diagnostics for persisted autopilot sessions."""
from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime

from deskagent.actions.productivity._common import (
    MAX_ITEMS, SESSION, ProductivityAction, limited, rows, status_counts,
    timestamp, with_session, with_store,
)
from deskagent.privacy.confirmation import redact

STEP = {**SESSION, "step_id": {"type": "string", "required": True}}


def _summary(session):
    steps = session.plan.steps
    completed = sum(step.status.value in {"succeeded", "skipped"} for step in steps)
    return {"session_id": session.id, "goal": session.goal[:500], "status": session.status.value,
            "mode": session.mode.value, "created_at": session.created_at,
            "updated_at": session.updated_at, "current_step_id": session.current_step_id,
            "completed_steps": completed, "total_steps": len(steps),
            "percent": round(completed * 100 / len(steps), 1) if steps else 0}


class ListTaskSessions(ProductivityAction):
    name = "list_task_sessions"
    description = "List persisted tasks with status and bounded progress"
    parameters_schema = {"status": {"type": "string", "required": False},
                         "limit": {"type": "integer", "required": False,
                                   "default": 50, "minimum": 1, "maximum": 200}}
    discoverable = True

    def execute(self, context, parameters):
        def operation(store):
            status = parameters.get("status")
            limit = parameters.get("limit", 50)
            if not 1 <= limit <= 200:
                raise ValueError("Limit must be 1-200")
            if status and status not in {
                "draft", "ready", "running", "waiting_for_user", "paused", "cancelling",
                "cancelled", "failed", "completed", "recovering",
            }:
                raise ValueError("Unknown task status")
            sessions = store.list((status,) if status else None)
            result = limited([_summary(item) for item in sessions], limit)
            return {"sessions": result["items"], "total": result["total"],
                    "truncated": result["truncated"]}
        return self.run(lambda: with_store(context, operation))


class GetTaskSummary(ProductivityAction):
    name = "get_task_summary"
    description = "Read compact task status, progress and current step"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: with_session(context, parameters["session_id"],
                                             lambda store, session: _summary(session)))


class GetTaskStepDetail(ProductivityAction):
    name = "get_task_step_detail"
    description = "Read one step's status, dependencies, retries and error"
    parameters_schema = STEP
    discoverable = True

    def execute(self, context, parameters):
        def operation(store, session):
            step = session.plan.step(parameters["step_id"])
            return {"session_id": session.id, "step_id": step.id, "title": step.title,
                    "action": step.action, "status": step.status.value,
                    "depends_on": list(step.depends_on), "attempts": step.attempts,
                    "retry_at": step.retry_at, "started_at": step.started_at,
                    "finished_at": step.finished_at, "error": step.error,
                    "error_code": step.error_code, "requires_confirmation": step.requires_confirmation}
        return self.run(lambda: with_session(context, parameters["session_id"], operation))


class GetTaskStepOutput(ProductivityAction):
    name = "get_task_step_output"
    description = "Read a bounded redacted output for one completed step"
    parameters_schema = STEP
    discoverable = True

    def execute(self, context, parameters):
        def operation(store, session):
            step = session.plan.step(parameters["step_id"])
            encoded = json.dumps(redact(step.output), ensure_ascii=False, default=str)
            return {"session_id": session.id, "step_id": step.id,
                    "output_json": encoded[:10000], "truncated": len(encoded) > 10000}
        return self.run(lambda: with_session(context, parameters["session_id"], operation))


class ListTaskEvents(ProductivityAction):
    name = "list_task_events"
    description = "Read bounded task event history after an event id"
    parameters_schema = {**SESSION, "after_id": {"type": "integer", "required": False,
                                                 "default": 0, "minimum": 0},
                         "limit": {"type": "integer", "required": False,
                                   "default": 100, "minimum": 1, "maximum": 500}}
    discoverable = True

    def execute(self, context, parameters):
        def operation(store, session):
            limit = parameters.get("limit", 100)
            if not 1 <= limit <= 500:
                raise ValueError("Limit must be 1-500")
            events = rows(context, session.id,
                          "SELECT id, timestamp, event, step_id, payload_json "
                          "FROM session_events WHERE session_id=? AND id>? ORDER BY id",
                          (parameters.get("after_id", 0),))
            selected = [{"id": item["id"], "timestamp": item["timestamp"],
                         "event": item["event"], "step_id": item["step_id"],
                         "payload": redact(json.loads(item["payload_json"]))}
                        for item in events[:limit]]
            return {"session_id": session.id, "events": selected,
                    "truncated": len(events) > limit,
                    "next_after_id": selected[-1]["id"] if selected else parameters.get("after_id", 0)}
        return self.run(lambda: with_session(context, parameters["session_id"], operation))


class GetTaskBlockers(ProductivityAction):
    name = "get_task_blockers"
    description = "Explain incomplete steps blocked by dependencies, approval or retry"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation(store, session):
            steps = {step.id: step for step in session.plan.steps}
            blockers = []
            for step in session.plan.steps:
                if step.status.value in {"succeeded", "skipped", "cancelled"}:
                    continue
                dependencies = [name for name in step.depends_on
                                if steps[name].status.value not in {"succeeded", "skipped"}]
                reasons = []
                if dependencies:
                    reasons.append("dependencies")
                if step.status.value == "waiting_for_user":
                    reasons.append("approval")
                if step.status.value == "retry_scheduled":
                    reasons.append("retry")
                if step.status.value == "failed":
                    reasons.append("failed")
                if reasons:
                    blockers.append({"step_id": step.id, "status": step.status.value,
                                     "reasons": reasons, "dependencies": dependencies,
                                     "retry_at": step.retry_at})
            return {"session_id": session.id, "blockers": blockers[:100],
                    "truncated": len(blockers) > 100}
        return self.run(lambda: with_session(context, parameters["session_id"], operation))


class GetTaskReadySteps(ProductivityAction):
    name = "get_task_ready_steps"
    description = "Identify pending steps whose dependencies have completed"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation(store, session):
            steps = {step.id: step for step in session.plan.steps}
            ready = []
            for step in session.plan.steps:
                if step.status.value in {"pending", "blocked", "ready"} and all(
                    steps[name].status.value in {"succeeded", "skipped"} for name in step.depends_on
                ):
                    ready.append(step)
            return {"session_id": session.id, "steps": [
                {"step_id": step.id, "title": step.title, "action": step.action,
                 "status": step.status.value} for step in ready[:100]
            ], "truncated": len(ready) > 100}
        return self.run(lambda: with_session(context, parameters["session_id"], operation))


class GetTaskRetrySchedule(ProductivityAction):
    name = "get_task_retry_schedule"
    description = "List scheduled retries with attempt counts and next times"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation(store, session):
            retries = [{"step_id": step.id, "attempts": step.attempts,
                        "max_attempts": step.retry.max_attempts, "retry_at": step.retry_at,
                        "error_code": step.error_code}
                       for step in session.plan.steps if step.status.value == "retry_scheduled"]
            return {"session_id": session.id, "retries": retries}
        return self.run(lambda: with_session(context, parameters["session_id"], operation))


class GetTaskDependencyGraph(ProductivityAction):
    name = "get_task_dependency_graph"
    description = "Read the dependency edges and status of each persisted step"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation(store, session):
            return {"session_id": session.id, "steps": [
                {"step_id": step.id, "depends_on": list(step.depends_on),
                 "status": step.status.value} for step in session.plan.steps
            ]}
        return self.run(lambda: with_session(context, parameters["session_id"], operation))


class GetTaskTimeline(ProductivityAction):
    name = "get_task_timeline"
    description = "Read timestamped task events without their payloads"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation(store, session):
            events = rows(context, session.id,
                          "SELECT id, timestamp, event, step_id FROM session_events "
                          "WHERE session_id=? ORDER BY id DESC")
            return {"session_id": session.id, "timeline": [
                {"id": item["id"], "timestamp": item["timestamp"],
                 "event": item["event"], "step_id": item["step_id"]}
                for item in reversed(events[:MAX_ITEMS])
            ], "truncated": len(events) > MAX_ITEMS}
        return self.run(lambda: with_session(context, parameters["session_id"], operation))


class GetTaskArtifacts(ProductivityAction):
    name = "get_task_artifacts"
    description = "List persisted task artifacts and their source steps"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation(store, session):
            artifacts = rows(context, session.id,
                             "SELECT id, step_id, kind, uri, created_at, metadata_json "
                             "FROM artifacts WHERE session_id=? ORDER BY id")
            return {"session_id": session.id, "artifacts": [
                {"id": item["id"], "step_id": item["step_id"], "kind": item["kind"],
                 "uri": item["uri"], "created_at": item["created_at"],
                 "metadata": redact(json.loads(item["metadata_json"]))}
                for item in artifacts[:100]
            ], "truncated": len(artifacts) > 100}
        return self.run(lambda: with_session(context, parameters["session_id"], operation))


class GetTaskAttempts(ProductivityAction):
    name = "get_task_attempts"
    description = "Read bounded step attempt outcomes from the task history"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            items = rows(context, parameters["session_id"],
                         "SELECT step_id, attempt, status, started_at, finished_at, error_code, error "
                         "FROM step_attempts WHERE session_id=? ORDER BY id")
            return {"session_id": parameters["session_id"], "attempts": items[:MAX_ITEMS],
                    "truncated": len(items) > MAX_ITEMS}
        return self.run(operation)


class GetTaskVerifications(ProductivityAction):
    name = "get_task_verifications"
    description = "Read bounded verification outcomes for a task"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            items = rows(context, parameters["session_id"],
                         "SELECT step_id, attempt, kind, success, created_at "
                         "FROM verifications WHERE session_id=? ORDER BY id")
            return {"session_id": parameters["session_id"], "verifications": items[:MAX_ITEMS],
                    "truncated": len(items) > MAX_ITEMS}
        return self.run(operation)


class GetTaskApprovals(ProductivityAction):
    name = "get_task_approvals"
    description = "Read approval status and timestamps without approval answers"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            items = rows(context, parameters["session_id"],
                         "SELECT confirmation_id, step_id, plan_version, status, created_at, answered_at "
                         "FROM approvals WHERE session_id=? ORDER BY created_at")
            return {"session_id": parameters["session_id"], "approvals": items[:MAX_ITEMS],
                    "truncated": len(items) > MAX_ITEMS}
        return self.run(operation)


class GetTaskToolCalls(ProductivityAction):
    name = "get_task_tool_calls"
    description = "Read action call status and timing without arguments or raw results"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation():
            items = rows(context, parameters["session_id"],
                         "SELECT id, step_id, attempt, action, status, started_at, finished_at "
                         "FROM tool_calls WHERE session_id=? ORDER BY started_at")
            return {"session_id": parameters["session_id"], "tool_calls": items[:MAX_ITEMS],
                    "truncated": len(items) > MAX_ITEMS}
        return self.run(operation)


class GetTaskStoreMetrics(ProductivityAction):
    name = "get_task_store_metrics"
    description = "Read aggregate task counts, completion rate, attempts and retries"
    parameters_schema = {}
    discoverable = True

    def execute(self, context, parameters):
        return self.run(lambda: with_store(context, lambda store: store.metrics()))


class GetTaskDuration(ProductivityAction):
    name = "get_task_duration"
    description = "Measure elapsed task time and remaining configured duration"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation(store, session):
            started = timestamp(session.started_at)
            now = datetime.now(UTC)
            deadline = session.deadline()
            return {"session_id": session.id, "started_at": session.started_at,
                    "elapsed_seconds": round((now - started).total_seconds(), 3) if started else None,
                    "deadline": deadline.isoformat() if deadline else None,
                    "remaining_seconds": round((deadline - now).total_seconds(), 3) if deadline else None}
        return self.run(lambda: with_session(context, parameters["session_id"], operation))


class CompareTaskSessions(ProductivityAction):
    name = "compare_task_sessions"
    description = "Compare statuses, progress and action usage of two tasks"
    parameters_schema = {"first_session_id": {"type": "string", "required": True},
                         "second_session_id": {"type": "string", "required": True}}
    discoverable = True

    def execute(self, context, parameters):
        def operation(store):
            first = store.get(parameters["first_session_id"])
            second = store.get(parameters["second_session_id"])
            first_actions = [step.action for step in first.plan.steps]
            second_actions = [step.action for step in second.plan.steps]
            return {"first": _summary(first), "second": _summary(second),
                    "same_plan_actions": first_actions == second_actions}
        return self.run(lambda: with_store(context, operation))


class GetTaskActionUsage(ProductivityAction):
    name = "get_task_action_usage"
    description = "Count planned actions and completed action outcomes"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation(store, session):
            counts = Counter(step.action for step in session.plan.steps)
            succeeded = Counter(step.action for step in session.plan.steps
                                if step.status.value == "succeeded")
            return {"session_id": session.id, "actions": [
                {"action": name, "planned": count, "succeeded": succeeded[name]}
                for name, count in counts.most_common(100)
            ], "truncated": len(counts) > 100}
        return self.run(lambda: with_session(context, parameters["session_id"], operation))


class GetTaskCompletionEvidence(ProductivityAction):
    name = "get_task_completion_evidence"
    description = "Summarize successful steps and persisted verification evidence"
    parameters_schema = SESSION
    discoverable = True

    def execute(self, context, parameters):
        def operation(store, session):
            succeeded = [step for step in session.plan.steps if step.status.value == "succeeded"]
            checks = rows(context, session.id,
                          "SELECT step_id, success FROM verifications WHERE session_id=? ORDER BY id")
            verified = Counter(item["step_id"] for item in checks if item["success"])
            return {"session_id": session.id, "status": session.status.value,
                    "status_counts": status_counts(session.plan.steps),
                    "successful_steps": [{"step_id": step.id, "action": step.action,
                                          "verified_checks": verified[step.id]}
                                         for step in succeeded[:100]],
                    "truncated": len(succeeded) > 100,
                    "verification_history_truncated": len(checks) > MAX_ITEMS}
        return self.run(lambda: with_session(context, parameters["session_id"], operation))
