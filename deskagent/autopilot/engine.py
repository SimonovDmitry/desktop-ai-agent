from __future__ import annotations

import hashlib
import json
import random
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from deskagent.agent.core.models import ActionExecution
from deskagent.agent.llm.response import ToolCall
from deskagent.autopilot.models import (
    AutopilotMode,
    FailurePolicy,
    Plan,
    Session,
    SessionStatus,
    Step,
    StepStatus,
    VerificationType,
    utc_now,
)
from deskagent.autopilot.store import SessionStore
from deskagent.autopilot.secrets import EnvironmentSecretProvider
from deskagent.autopilot.validation import PlanValidator
from deskagent.privacy.confirmation import ConfirmationRequest, PreviewBuilder


TERMINAL_SESSIONS = {SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED}
TERMINAL_STEPS = {StepStatus.SUCCEEDED, StepStatus.SKIPPED, StepStatus.FAILED, StepStatus.CANCELLED}
SUCCESS_STEPS = {StepStatus.SUCCEEDED, StepStatus.SKIPPED}
ACTIVE_STEPS = {StepStatus.RUNNING, StepStatus.VERIFYING}


class InvalidSessionTransition(RuntimeError):
    pass


class AutopilotEngine:
    """Durable, resumable scheduler around the existing action catalog."""

    def __init__(self, catalog, store: SessionStore, sleep=time.sleep, max_steps: int = 100,
                 max_parallelism: int = 4, owner_id: str | None = None, planner=None):
        self.catalog = catalog
        self.store = store
        self.sleep = sleep
        self.max_parallelism = max(1, max_parallelism)
        self.owner_id = owner_id or f"worker_{uuid.uuid4().hex}"
        self.planner = planner
        self.secret_provider = EnvironmentSecretProvider()
        self.validator = PlanValidator(catalog.registry, max_steps=max_steps)

    def create_session(self, goal: str, plan: Plan | dict[str, Any],
                       mode: AutopilotMode = AutopilotMode.GUIDED,
                       max_duration_seconds: float = 3600,
                       max_replans: int = 3, dry_run: bool = False) -> Session:
        if not goal.strip():
            raise ValueError("Session goal cannot be empty")
        plan = Plan.from_dict(plan) if isinstance(plan, dict) else plan
        self.validator.validate(plan)
        session = Session(
            goal.strip(), deepcopy(plan), status=SessionStatus.READY, mode=mode,
            max_duration_seconds=max_duration_seconds, max_replans=max_replans,
            dry_run=dry_run,
        )
        return self.store.create(session)

    def create_from_goal(self, goal: str, mode: AutopilotMode = AutopilotMode.GUIDED) -> Session:
        if not self.planner:
            raise RuntimeError("A plan service is not configured")
        return self.create_session(goal, self.planner.create_plan(goal, self.catalog.schemas()), mode)

    def start(self, session_id: str) -> Session:
        session = self.store.get(session_id)
        if session.status not in {SessionStatus.READY, SessionStatus.PAUSED, SessionStatus.RECOVERING}:
            raise InvalidSessionTransition(f"Cannot start session in {session.status.value}")
        session.status = SessionStatus.RUNNING
        session.started_at = session.started_at or utc_now()
        if session.mode is AutopilotMode.AUTOPILOT and not session.approved_plan_hash:
            session.approved_plan_hash = self._plan_hash(session.plan)
        self.store.save(session, "session_started")
        return self.run_until_idle(session_id)

    def resume(self, session_id: str) -> Session:
        return self.start(session_id)

    def run_until_idle(self, session_id: str) -> Session:
        if not self.store.acquire_lease(session_id, self.owner_id):
            return self.store.get(session_id)
        try:
            while True:
                session = self.store.get(session_id)
                if session.status is not SessionStatus.RUNNING:
                    return session
                if self._expired(session):
                    session.status, session.error = SessionStatus.FAILED, "Session duration limit exceeded"
                    return self.store.save(session, "session_failed", payload={"error_code": "SESSION_TIMEOUT"})
                progressed = self.tick(session_id)
                current = self.store.get(session_id)
                if not progressed or current.status is not SessionStatus.RUNNING:
                    return current
        finally:
            self.store.release_lease(session_id, self.owner_id)

    def tick(self, session_id: str) -> bool:
        session = self.store.get(session_id)
        if session.status is not SessionStatus.RUNNING:
            return False
        ready = self._ready_steps(session)
        if not ready:
            if any(step.status is StepStatus.RETRY_SCHEDULED for step in session.plan.steps):
                self.store.save(session)
                return False
            self._finish_or_block(session)
            return False

        selected = self._select_non_conflicting(ready)
        prepared = []
        for step in selected:
            if not self._condition_matches(step, session):
                step.status, step.finished_at = StepStatus.SKIPPED, utc_now()
                self.store.save(session, "step_skipped", step.id, {"reason": "condition_false"})
                continue
            arguments = self._resolve(step.arguments, session)
            call = ToolCall(step.action, arguments, f"{session.id}:{step.id}")
            decision = self.catalog.policy_for(call, session.action_count)
            self.catalog.audit_decision(call, decision, session.id)
            if not decision.allowed:
                self._handle_failure(session, step, decision.reason or "Action denied", decision.reason_code)
                continue
            if self._needs_confirmation(session, step, decision) and not step.confirmation_approved:
                self._request_confirmation(session, step, arguments, decision)
                return True
            if not self.store.acquire_resources(step.resources, session.id, step.id, self.owner_id):
                step.status = StepStatus.BLOCKED
                continue
            step.status = StepStatus.RUNNING
            step.attempts += 1
            step.first_attempt_at = step.first_attempt_at or utc_now()
            step.started_at = utc_now()
            step.retry_at = None
            step.idempotency_key = step.idempotency_key or (
                f"{session.id}:{session.plan.version}:{step.id}" if step.idempotent else None
            )
            session.current_step_id = step.id
            self.store.begin_attempt(session.id, step.id, step.attempts)
            self.store.save(session, "step_started", step.id, {"attempt": step.attempts})
            prepared.append((step, arguments, decision))

        if not prepared:
            self.store.save(session)
            return bool(selected)
        self._execute_wave(session.id, prepared)
        return True

    def pause(self, session_id: str) -> Session:
        session = self.store.get(session_id)
        if session.status not in {SessionStatus.RUNNING, SessionStatus.READY}:
            raise InvalidSessionTransition(f"Cannot pause session in {session.status.value}")
        session.status = SessionStatus.PAUSED
        return self.store.save(session, "session_paused")

    def cancel(self, session_id: str, compensate: bool = False) -> Session:
        session = self.store.get(session_id)
        if session.status in TERMINAL_SESSIONS:
            return session
        if compensate and any(step.compensation and step.status is StepStatus.SUCCEEDED
                              for step in session.plan.steps):
            return self.request_compensation(session_id)
        session.status = SessionStatus.CANCELLING
        self.store.save(session, "session_cancelling")
        return self._finish_cancellation(self.store.get(session_id))

    def approve(self, session_id: str, answer: bool | dict[str, Any], text: str | None = None) -> Session:
        session = self.store.get(session_id)
        pending = session.pending_confirmation
        if session.status is not SessionStatus.WAITING_FOR_USER or not pending:
            raise InvalidSessionTransition("Session is not waiting for confirmation")
        if pending.get("plan_version") != session.plan.version:
            raise InvalidSessionTransition("The plan changed after confirmation was requested")
        request = ConfirmationRequest.from_dict(pending)
        if isinstance(answer, bool):
            answer = {"approved": answer, "confirmation_id": request.confirmation_id, "text": text}
        approved = request.verify(answer)
        self.store.answer_approval(request.confirmation_id, answer, "approved" if approved else "denied")
        step_id = pending.get("step_id")
        session.pending_confirmation = None
        if not approved:
            session.status = SessionStatus.CANCELLED
            if step_id:
                session.plan.step(step_id).status = StepStatus.CANCELLED
            return self.store.save(session, "confirmation_denied", step_id)
        if pending.get("kind") == "compensation":
            session.status = SessionStatus.CANCELLING
            self.store.save(session, "confirmation_approved")
            return self._execute_compensations(session)
        if pending.get("kind") == "plan":
            session.approved_plan_hash = pending["scope_hash"]
        elif step_id:
            step = session.plan.step(step_id)
            current_arguments = self._resolve(step.arguments, session)
            if self._scope_hash(step.action, current_arguments, session.plan.version) != pending["scope_hash"]:
                raise InvalidSessionTransition("Action arguments changed after confirmation was requested")
            step.confirmation_approved = True
            step.status = StepStatus.PENDING
        session.status = SessionStatus.RUNNING
        self.store.save(session, "confirmation_approved", step_id)
        return self.run_until_idle(session.id)

    def retry_step(self, session_id: str, step_id: str) -> Session:
        session = self.store.get(session_id)
        step = session.plan.step(step_id)
        if step.status not in {StepStatus.FAILED, StepStatus.WAITING_FOR_USER}:
            raise InvalidSessionTransition(f"Step {step_id} cannot be retried from {step.status.value}")
        step.status, step.error, step.error_code = StepStatus.PENDING, None, None
        step.retry_at = None
        session.status, session.error = SessionStatus.RUNNING, None
        self.store.save(session, "step_retry_requested", step.id)
        return self.run_until_idle(session.id)

    def skip_step(self, session_id: str, step_id: str) -> Session:
        session = self.store.get(session_id)
        step = session.plan.step(step_id)
        if step.status in TERMINAL_STEPS:
            raise InvalidSessionTransition(f"Step {step_id} is already terminal")
        step.status, step.finished_at = StepStatus.SKIPPED, utc_now()
        session.status = SessionStatus.RUNNING
        self.store.save(session, "step_skipped", step.id)
        return self.run_until_idle(session.id)

    def revise_plan(self, session_id: str, plan: Plan | dict[str, Any], reason: str) -> Session:
        session = self.store.get(session_id)
        if session.replan_count >= session.max_replans:
            raise InvalidSessionTransition("Replanning limit exceeded")
        replacement = Plan.from_dict(plan) if isinstance(plan, dict) else plan
        self.validator.validate(replacement)
        old = {step.id: step for step in session.plan.steps}
        for step in replacement.steps:
            previous = old.get(step.id)
            unchanged = previous and previous.action == step.action and previous.arguments == step.arguments
            if unchanged and previous.status in SUCCESS_STEPS:
                step.status, step.attempts, step.output = previous.status, previous.attempts, previous.output
        replacement.version = session.plan.version + 1
        session.plan = replacement
        session.replan_count += 1
        session.status, session.current_step_id = SessionStatus.READY, None
        session.pending_confirmation = None
        session.approved_plan_hash = None
        return self.store.save_plan(session, reason)

    def recover_incomplete(self) -> list[Session]:
        statuses = tuple(item.value for item in (
            SessionStatus.RUNNING, SessionStatus.CANCELLING, SessionStatus.RECOVERING,
        ))
        recovered = []
        for session in self.store.list(statuses):
            if session.status is SessionStatus.CANCELLING:
                recovered.append(self._finish_cancellation(session))
                continue
            session.status = SessionStatus.RECOVERING
            uncertain = None
            for step in session.plan.steps:
                if step.status is StepStatus.RETRY_SCHEDULED:
                    continue
                if step.status in ACTIVE_STEPS:
                    if step.idempotent:
                        step.status = StepStatus.PENDING
                    else:
                        step.status = StepStatus.WAITING_FOR_USER
                        uncertain = step
            if uncertain:
                session.status = SessionStatus.WAITING_FOR_USER
                self._request_confirmation(
                    session, uncertain, self._resolve(uncertain.arguments, session),
                    self.catalog.policy_for(ToolCall(uncertain.action, uncertain.arguments), session.action_count),
                    kind="uncertain_result",
                )
            else:
                session.status = SessionStatus.READY
                self.store.save(session, "session_recovered")
            recovered.append(self.store.get(session.id))
        return recovered

    def request_compensation(self, session_id: str) -> Session:
        session = self.store.get(session_id)
        calls = []
        for step in reversed(session.plan.steps):
            if step.status is StepStatus.SUCCEEDED and step.compensation:
                arguments = self._resolve(step.compensation.arguments, session)
                calls.append({
                    "id": step.id, "name": step.compensation.action, "args": arguments,
                    "policy": {"risk": "high", "confirmation_kind": "approve"},
                })
        if not calls:
            return self.cancel(session_id)
        request = PreviewBuilder.build(calls)
        scope_hash = self._plan_hash(session.plan)
        pending = {
            **request.to_dict(), "kind": "compensation", "step_id": None,
            "plan_version": session.plan.version, "scope_hash": scope_hash,
        }
        session.status, session.pending_confirmation = SessionStatus.WAITING_FOR_USER, pending
        self.store.put_approval(request.confirmation_id, session.id, None,
                                session.plan.version, scope_hash, pending)
        return self.store.save(session, "compensation_confirmation_requested")

    def _execute_wave(self, session_id: str, prepared):
        pool = ThreadPoolExecutor(max_workers=min(self.max_parallelism, len(prepared)))
        futures = {}
        for step, arguments, decision in prepared:
            futures[pool.submit(self._execute_action, session_id, step, arguments, decision)] = step.id
        for future, step_id in futures.items():
            session = self.store.get(session_id)
            step = session.plan.step(step_id)
            timeout = step.timeout_seconds
            try:
                execution = future.result(timeout=timeout)
            except TimeoutError:
                execution = ActionExecution(
                    f"timeout:{session.id}:{step.id}", step.action,
                    self._resolve(step.arguments, session), False,
                    error=f"Step timed out after {timeout} seconds", error_code="TIMEOUT",
                )
            finally:
                self.store.release_resources(session.id, step.id, self.owner_id)
            current = self.store.get(session_id)
            if current.status is SessionStatus.CANCELLED:
                continue
            step = current.plan.step(step_id)
            self._apply_execution(current, step, execution)
        pool.shutdown(wait=False, cancel_futures=True)

    def _execute_action(self, session_id, step, arguments, decision):
        call_id = f"{session_id}:{step.id}:{uuid.uuid4().hex[:10]}"
        cached = self.store.completed_tool_call(step.idempotency_key)
        if cached:
            return ActionExecution.from_dict(cached)
        self.store.start_tool_call(call_id, session_id, step.id, step.attempts,
                                   step.action, arguments, step.idempotency_key)
        call = ToolCall(step.action, arguments, call_id)
        if decision.dry_run or self.store.get(session_id).dry_run:
            execution = ActionExecution(call_id, step.action, arguments, True,
                                        {"dry_run": True, "action": step.action})
        else:
            execution = self.catalog.execute(call, session_id, decision.risk.value)
        self.store.finish_tool_call(call_id, "succeeded" if execution.success else "failed",
                                    execution.to_dict())
        return execution

    def _apply_execution(self, session: Session, step: Step, execution: ActionExecution):
        session.action_count += 1
        if execution.success:
            step.status = StepStatus.VERIFYING
            step.output = execution.data
            self.store.save(session, "step_verifying", step.id)
            verified, error = self._verify_all(session, step, execution)
            if verified:
                step.status, step.finished_at = StepStatus.SUCCEEDED, utc_now()
                step.error = step.error_code = None
                session.current_step_id = None
                self.store.finish_attempt(session.id, step.id, step.attempts, "succeeded")
                self.store.save(session, "step_completed", step.id, {"output": execution.data})
                return
            execution = ActionExecution(**{
                **execution.to_dict(), "verified": False, "verification_error": error,
            })
        code = execution.error_code or (
            "VERIFICATION_FAILED" if execution.verified is False else "ACTION_FAILED"
        )
        error = execution.error or execution.verification_error or "Step failed"
        self.store.finish_attempt(session.id, step.id, step.attempts, "failed", code, error)
        if self._schedule_retry(session, step, code):
            return
        self._handle_failure(session, step, error, code)

    def _verify_all(self, session: Session, step: Step, execution: ActionExecution):
        for verification in step.verifications:
            deadline = time.monotonic() + verification.timeout_seconds
            while True:
                success, error, details = self._run_verification(session, step, execution, verification)
                self.store.add_verification(session.id, step.id, step.attempts,
                                            verification.type.value, success, details)
                if success:
                    break
                if not verification.timeout_seconds or time.monotonic() >= deadline:
                    return False, error
                control = self.store.get(session.id)
                if control.status is not SessionStatus.RUNNING:
                    return False, "Verification interrupted"
                self.sleep(min(verification.interval_seconds,
                               max(0.0, deadline - time.monotonic())))
        return True, None

    def _run_verification(self, session, step, execution, verification):
        arguments = self._resolve(verification.arguments, session)
        if verification.type is VerificationType.CATALOG:
            result = self.catalog.verify(execution)
            return result.verified is not False, result.verification_error, result.to_dict()
        if verification.type is VerificationType.OUTPUT_EQUALS:
            actual = execution.data
            for part in str(arguments.get("path", "")).split("."):
                if part:
                    actual = actual.get(part) if isinstance(actual, dict) else getattr(actual, part, None)
            expected = arguments.get("expected")
            return actual == expected, f"Expected {expected!r}, got {actual!r}", {"actual": actual}
        if verification.type is VerificationType.FILE_EXISTS:
            exists = Path(str(arguments["path"])).expanduser().exists()
            expected = arguments.get("exists", True)
            return exists is expected, f"File existence is {exists}, expected {expected}", {"exists": exists}
        if verification.type is VerificationType.ACTION:
            call = ToolCall(arguments["action"], arguments.get("arguments", {}))
            decision = self.catalog.policy_for(call, session.action_count)
            if not decision.allowed or decision.confirmation_required:
                return False, "Verification action is not allowed without confirmation", {}
            result = self.catalog.execute(call, session.id, decision.risk.value)
            return result.success, result.error, result.to_dict()
        return False, "Unsupported verification", {}

    def _schedule_retry(self, session, step, code):
        elapsed_ok = True
        if step.retry.max_elapsed_seconds is not None and step.first_attempt_at:
            elapsed = (datetime.now(UTC) - datetime.fromisoformat(step.first_attempt_at)).total_seconds()
            elapsed_ok = elapsed < step.retry.max_elapsed_seconds
        can_retry = (
            code in step.retry.retry_on and step.attempts < step.retry.max_attempts
            and step.idempotent and elapsed_ok
        )
        if not can_retry:
            return False
        delay = step.retry.delay_for(step.attempts, random.uniform(-1, 1))
        step.status = StepStatus.RETRY_SCHEDULED
        step.retry_at = datetime.fromtimestamp(datetime.now(UTC).timestamp() + delay, UTC).isoformat()
        self.store.save(session, "step_retry_scheduled", step.id, {
            "attempt": step.attempts, "retry_at": step.retry_at, "error_code": code,
        })
        return True

    def _handle_failure(self, session, step, error, code):
        step.error, step.error_code, step.finished_at = error, code, utc_now()
        session.current_step_id = None
        if step.on_failure is FailurePolicy.SKIP:
            step.status = StepStatus.SKIPPED
            self.store.save(session, "step_skipped", step.id, {"error": error, "error_code": code})
            return
        if step.on_failure is FailurePolicy.REPLAN and self.planner and session.replan_count < session.max_replans:
            replacement = self.planner.replan(session, step, error, self.catalog.schemas())
            self.revise_plan(session.id, replacement, f"step {step.id} failed: {error}")
            revised = self.store.get(session.id)
            revised.status = SessionStatus.RUNNING
            self.store.save(revised, "session_replanned")
            return
        if step.on_failure is FailurePolicy.COMPENSATE:
            step.status = StepStatus.FAILED
            session.status, session.error = SessionStatus.FAILED, error
            self.store.save(session, "step_failed", step.id, {"error": error, "error_code": code})
            self.request_compensation(session.id)
            return
        step.status = StepStatus.FAILED
        session.status, session.error = SessionStatus.FAILED, error
        self.store.save(session, "step_failed", step.id, {"error": error, "error_code": code})
        self.store.finish_workflow_runs(session.id, session.status.value)

    def _ready_steps(self, session):
        now = datetime.now(UTC)
        statuses = {step.id: step.status for step in session.plan.steps}
        ready = []
        for step in session.plan.steps:
            eligible = step.status in {StepStatus.PENDING, StepStatus.BLOCKED, StepStatus.READY}
            if step.status is StepStatus.RETRY_SCHEDULED:
                eligible = bool(step.retry_at and datetime.fromisoformat(step.retry_at) <= now)
            if not eligible:
                continue
            if all(statuses.get(item) in SUCCESS_STEPS for item in step.depends_on):
                step.status = StepStatus.READY
                ready.append(step)
            else:
                step.status = StepStatus.BLOCKED
        return ready

    def _select_non_conflicting(self, ready):
        selected, resources = [], set()
        for step in ready:
            if len(selected) >= self.max_parallelism:
                break
            if resources.isdisjoint(step.resources):
                selected.append(step)
                resources.update(step.resources)
        return selected

    def _finish_or_block(self, session):
        if all(step.status in SUCCESS_STEPS for step in session.plan.steps):
            session.status, session.current_step_id = SessionStatus.COMPLETED, None
            result = self.store.save(session, "session_completed")
            self.store.finish_workflow_runs(session.id, session.status.value)
            return result
        if any(step.status in ACTIVE_STEPS for step in session.plan.steps):
            return self.store.save(session)
        failed = next((step for step in session.plan.steps if step.status is StepStatus.FAILED), None)
        session.status = SessionStatus.FAILED
        session.error = failed.error if failed else "Plan cannot make progress"
        result = self.store.save(session, "session_failed", failed.id if failed else None)
        self.store.finish_workflow_runs(session.id, session.status.value)
        return result

    def _finish_cancellation(self, session):
        for step in session.plan.steps:
            if step.status not in TERMINAL_STEPS:
                step.status, step.finished_at = StepStatus.CANCELLED, utc_now()
        session.current_step_id = None
        session.pending_confirmation = None
        session.status = SessionStatus.CANCELLED
        result = self.store.save(session, "session_cancelled")
        self.store.finish_workflow_runs(session.id, session.status.value)
        return result

    def _execute_compensations(self, session):
        failures = []
        for step in reversed(session.plan.steps):
            if step.status is not StepStatus.SUCCEEDED or not step.compensation:
                continue
            arguments = self._resolve(step.compensation.arguments, session)
            call = ToolCall(step.compensation.action, arguments)
            decision = self.catalog.policy_for(call, session.action_count)
            if not decision.allowed:
                failures.append({"step_id": step.id, "error": decision.reason})
                continue
            result = self.catalog.execute(call, session.id, decision.risk.value)
            session.action_count += 1
            if not result.success:
                failures.append({"step_id": step.id, "error": result.error})
            self.store.save(session, "step_compensated", step.id, {
                "success": result.success, "error": result.error,
            })
        session.status = SessionStatus.FAILED if failures else SessionStatus.CANCELLED
        session.error = f"Compensation failures: {failures}" if failures else None
        return self.store.save(session, "compensation_completed", payload={"failures": failures})

    def _request_confirmation(self, session, step, arguments, decision, kind="action"):
        policy = decision.to_dict()
        request = PreviewBuilder.build([{
            "id": f"{session.id}:{session.plan.version}:{step.id}",
            "name": step.action, "args": arguments, "policy": policy,
        }])
        scope_hash = self._scope_hash(step.action, arguments, session.plan.version)
        pending = {
            **request.to_dict(), "kind": kind, "step_id": step.id,
            "plan_version": session.plan.version, "scope_hash": scope_hash,
        }
        session.status = SessionStatus.WAITING_FOR_USER
        session.pending_confirmation = pending
        step.status = StepStatus.WAITING_FOR_USER
        self.store.put_approval(request.confirmation_id, session.id, step.id,
                                session.plan.version, scope_hash, pending)
        return self.store.save(session, "confirmation_requested", step.id, pending)

    def _needs_confirmation(self, session, step, decision):
        if session.mode is AutopilotMode.MANUAL:
            return True
        if session.mode is AutopilotMode.GUIDED:
            return step.requires_confirmation or decision.confirmation_required
        plan_changed = session.approved_plan_hash != self._plan_hash(session.plan)
        return plan_changed or decision.confirmation_required

    def _condition_matches(self, step, session):
        if not step.condition:
            return True
        condition = self._resolve(step.condition, session)
        if "equals" in condition:
            return condition["equals"].get("left") == condition["equals"].get("right")
        if "not_equals" in condition:
            return condition["not_equals"].get("left") != condition["not_equals"].get("right")
        if "all" in condition:
            return all(self._condition_matches(Step("condition", "condition", step.action,
                                                    condition=item), session)
                       for item in condition["all"])
        if "any" in condition:
            return any(self._condition_matches(Step("condition", "condition", step.action,
                                                    condition=item), session)
                       for item in condition["any"])
        raise ValueError(f"Unsupported condition for step {step.id}")

    def _resolve(self, value: Any, session: Session) -> Any:
        if isinstance(value, dict):
            return {key: self._resolve(item, session) for key, item in value.items()}
        if isinstance(value, list):
            return [self._resolve(item, session) for item in value]
        if not isinstance(value, str) or not value.startswith("${steps.") or not value.endswith("}"):
            if isinstance(value, str) and value.startswith("${secrets.") and value.endswith("}"):
                return self.secret_provider.get(value[10:-1])
            return value
        expression = value[2:-1].split(".")
        if len(expression) < 3 or expression[2] != "output":
            return value
        output = session.plan.step(expression[1]).output
        for part in expression[3:]:
            output = output[part] if isinstance(output, dict) else getattr(output, part)
        return output

    @staticmethod
    def _scope_hash(action, arguments, plan_version):
        raw = json.dumps({"action": action, "arguments": arguments, "plan_version": plan_version},
                         ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _plan_hash(plan):
        raw = json.dumps(plan.definition_dict(), ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _expired(session):
        deadline = session.deadline()
        return bool(deadline and datetime.now(UTC) >= deadline)
