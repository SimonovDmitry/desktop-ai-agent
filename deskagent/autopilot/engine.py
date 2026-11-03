from __future__ import annotations

import re
import time
import uuid
from copy import deepcopy
from typing import Any

from deskagent.agent.llm.response import ToolCall
from deskagent.autopilot.models import (
    AutopilotMode,
    FailurePolicy,
    Plan,
    Session,
    SessionStatus,
    Step,
    StepStatus,
)
from deskagent.autopilot.store import SessionStore
from deskagent.autopilot.validation import PlanValidator


TERMINAL_SESSIONS = {SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED}
TERMINAL_STEPS = {StepStatus.SUCCEEDED, StepStatus.SKIPPED, StepStatus.FAILED, StepStatus.CANCELLED}
SUCCESS_STEPS = {StepStatus.SUCCEEDED, StepStatus.SKIPPED}
REFERENCE = re.compile(r"^\$\{steps\.([A-Za-z0-9_-]+)\.output(?:\.([A-Za-z0-9_.-]+))?\}$")


class InvalidSessionTransition(RuntimeError):
    pass


class AutopilotEngine:
    """Deterministic durable executor around the existing action catalog."""

    def __init__(self, catalog, store: SessionStore, sleep=time.sleep, max_steps: int = 100):
        self.catalog = catalog
        self.store = store
        self.sleep = sleep
        self.validator = PlanValidator(catalog.registry, max_steps=max_steps)

    def create_session(
        self, goal: str, plan: Plan | dict[str, Any], mode: AutopilotMode = AutopilotMode.GUIDED
    ) -> Session:
        if not goal.strip():
            raise ValueError("Session goal cannot be empty")
        plan = Plan.from_dict(plan) if isinstance(plan, dict) else plan
        self.validator.validate(plan)
        session = Session(goal.strip(), deepcopy(plan), status=SessionStatus.READY, mode=mode)
        return self.store.create(session)

    def start(self, session_id: str) -> Session:
        session = self.store.get(session_id)
        if session.status not in {SessionStatus.READY, SessionStatus.PAUSED, SessionStatus.RECOVERING}:
            raise InvalidSessionTransition(f"Cannot start session in {session.status.value}")
        session.status = SessionStatus.RUNNING
        self.store.save(session, "session_started")
        return self._run(session)

    def resume(self, session_id: str) -> Session:
        return self.start(session_id)

    def pause(self, session_id: str) -> Session:
        session = self.store.get(session_id)
        if session.status not in {SessionStatus.RUNNING, SessionStatus.READY}:
            raise InvalidSessionTransition(f"Cannot pause session in {session.status.value}")
        session.status = SessionStatus.PAUSED
        return self.store.save(session, "session_paused")

    def cancel(self, session_id: str) -> Session:
        session = self.store.get(session_id)
        if session.status in TERMINAL_SESSIONS:
            return session
        session.status = SessionStatus.CANCELLING
        self.store.save(session, "session_cancelling")
        for step in session.plan.steps:
            if step.status not in TERMINAL_STEPS:
                step.status = StepStatus.CANCELLED
        session.current_step_id = None
        session.pending_confirmation = None
        session.status = SessionStatus.CANCELLED
        return self.store.save(session, "session_cancelled")

    def approve(self, session_id: str, approved: bool) -> Session:
        session = self.store.get(session_id)
        if session.status is not SessionStatus.WAITING_FOR_USER or not session.pending_confirmation:
            raise InvalidSessionTransition("Session is not waiting for confirmation")
        step = session.plan.step(session.pending_confirmation["step_id"])
        session.pending_confirmation = None
        if not approved:
            step.status = StepStatus.CANCELLED
            session.status = SessionStatus.CANCELLED
            return self.store.save(session, "confirmation_denied", step.id)
        step.confirmation_approved = True
        step.status = StepStatus.PENDING
        session.status = SessionStatus.RUNNING
        self.store.save(session, "confirmation_approved", step.id)
        return self._run(session)

    def retry_step(self, session_id: str, step_id: str) -> Session:
        session = self.store.get(session_id)
        step = session.plan.step(step_id)
        if step.status not in {StepStatus.FAILED, StepStatus.WAITING_FOR_USER}:
            raise InvalidSessionTransition(f"Step {step_id} cannot be retried from {step.status.value}")
        step.status, step.error, step.error_code = StepStatus.PENDING, None, None
        session.status, session.error = SessionStatus.RUNNING, None
        self.store.save(session, "step_retry_requested", step.id)
        return self._run(session)

    def skip_step(self, session_id: str, step_id: str) -> Session:
        session = self.store.get(session_id)
        step = session.plan.step(step_id)
        if step.status in TERMINAL_STEPS:
            raise InvalidSessionTransition(f"Step {step_id} is already terminal")
        step.status = StepStatus.SKIPPED
        session.status = SessionStatus.RUNNING
        self.store.save(session, "step_skipped", step.id)
        return self._run(session)

    def revise_plan(self, session_id: str, plan: Plan | dict[str, Any], reason: str) -> Session:
        session = self.store.get(session_id)
        replacement = Plan.from_dict(plan) if isinstance(plan, dict) else plan
        self.validator.validate(replacement)
        old = {step.id: step for step in session.plan.steps}
        for step in replacement.steps:
            previous = old.get(step.id)
            if previous and previous.status in SUCCESS_STEPS and previous.action == step.action:
                step.status, step.attempts, step.output = previous.status, previous.attempts, previous.output
        replacement.version = session.plan.version + 1
        session.plan = replacement
        session.status = SessionStatus.READY
        session.current_step_id = None
        session.pending_confirmation = None
        return self.store.save_plan(session, reason)

    def recover_incomplete(self) -> list[Session]:
        statuses = (
            SessionStatus.RUNNING.value,
            SessionStatus.CANCELLING.value,
            SessionStatus.RECOVERING.value,
        )
        recovered = []
        for session in self.store.list(statuses):
            session.status = SessionStatus.RECOVERING
            running = next((step for step in session.plan.steps if step.status is StepStatus.RUNNING), None)
            if running and not running.idempotent:
                running.status = StepStatus.WAITING_FOR_USER
                session.status = SessionStatus.WAITING_FOR_USER
                session.pending_confirmation = {
                    "kind": "uncertain_result",
                    "step_id": running.id,
                    "question": "The application stopped during this action. Retry it?",
                }
            elif running:
                running.status = StepStatus.PENDING
                session.status = SessionStatus.READY
            else:
                session.status = SessionStatus.READY
            self.store.save(session, "session_recovered", running.id if running else None)
            recovered.append(session)
        return recovered

    def _run(self, session: Session) -> Session:
        while session.status is SessionStatus.RUNNING:
            ready = self._ready_steps(session)
            if not ready:
                return self._finish_or_block(session)
            step = ready[0]
            if not self._condition_matches(step, session):
                step.status = StepStatus.SKIPPED
                self.store.save(session, "step_skipped", step.id, {"reason": "condition_false"})
                continue
            arguments = self._resolve(step.arguments, session)
            decision = self.catalog.policy_for(ToolCall(step.action, arguments, f"{session.id}:{step.id}"))
            if not decision.allowed:
                return self._fail(session, step, decision.reason or "Action denied", decision.reason_code)
            needs_confirmation = (
                session.mode is AutopilotMode.MANUAL
                or step.requires_confirmation
                or decision.confirmation_required
            )
            if needs_confirmation and not step.confirmation_approved:
                step.status = StepStatus.WAITING_FOR_USER
                session.status = SessionStatus.WAITING_FOR_USER
                session.pending_confirmation = {
                    "kind": "action",
                    "step_id": step.id,
                    "action": step.action,
                    "arguments": arguments,
                    "risk": decision.risk.value,
                    "question": f"Approve step: {step.title}?",
                }
                return self.store.save(session, "confirmation_requested", step.id, session.pending_confirmation)
            self._execute_step(session, step, arguments, decision.risk.value)
        return session

    def _execute_step(self, session: Session, step: Step, arguments: dict[str, Any], risk: str):
        while step.attempts < step.retry.max_attempts:
            step.status = StepStatus.RUNNING
            step.attempts += 1
            session.current_step_id = step.id
            self.store.save(session, "step_started", step.id, {"attempt": step.attempts})
            call = ToolCall(step.action, arguments, f"{session.id}:{step.id}:{uuid.uuid4().hex[:8]}")
            execution = self.catalog.execute(call, session.id, risk)
            if execution.success:
                step.status = StepStatus.VERIFYING
                self.store.save(session, "step_verifying", step.id)
                execution = self.catalog.verify(execution)
            if execution.success and execution.verified is not False:
                step.status, step.output = StepStatus.SUCCEEDED, execution.data
                step.error = step.error_code = None
                session.current_step_id = None
                self.store.save(session, "step_completed", step.id, {"output": execution.data})
                return

            code = execution.error_code or ("VERIFICATION_FAILED" if execution.verified is False else "ACTION_FAILED")
            error = execution.error or execution.verification_error or "Step failed"
            can_retry = code in step.retry.retry_on and step.attempts < step.retry.max_attempts and step.idempotent
            if can_retry:
                delay = step.retry.delay_for(step.attempts)
                step.status = StepStatus.RETRY_SCHEDULED
                self.store.save(
                    session, "step_retry_scheduled", step.id,
                    {"attempt": step.attempts, "delay_seconds": delay, "error_code": code},
                )
                self.sleep(delay)
                continue
            self._fail(session, step, error, code)
            return

    def _fail(self, session: Session, step: Step, error: str, code: str | None) -> Session:
        step.error, step.error_code = error, code
        session.current_step_id = None
        if step.on_failure is FailurePolicy.SKIP:
            step.status = StepStatus.SKIPPED
            self.store.save(session, "step_skipped", step.id, {"error": error, "error_code": code})
            return session
        step.status = StepStatus.FAILED
        session.status, session.error = SessionStatus.FAILED, error
        return self.store.save(session, "step_failed", step.id, {"error": error, "error_code": code})

    def _ready_steps(self, session: Session) -> list[Step]:
        statuses = {step.id: step.status for step in session.plan.steps}
        ready = []
        for step in session.plan.steps:
            if step.status not in {StepStatus.PENDING, StepStatus.BLOCKED, StepStatus.READY}:
                continue
            if all(statuses.get(item) in SUCCESS_STEPS for item in step.depends_on):
                step.status = StepStatus.READY
                ready.append(step)
            else:
                step.status = StepStatus.BLOCKED
        return ready

    def _finish_or_block(self, session: Session) -> Session:
        if all(step.status in SUCCESS_STEPS for step in session.plan.steps):
            session.status, session.current_step_id = SessionStatus.COMPLETED, None
            return self.store.save(session, "session_completed")
        failed = next((step for step in session.plan.steps if step.status is StepStatus.FAILED), None)
        session.status = SessionStatus.FAILED
        session.error = failed.error if failed else "Plan cannot make progress"
        return self.store.save(session, "session_failed", failed.id if failed else None)

    def _condition_matches(self, step: Step, session: Session) -> bool:
        if not step.condition:
            return True
        condition = self._resolve(step.condition, session)
        if "equals" in condition:
            values = condition["equals"]
            return values.get("left") == values.get("right")
        if "not_equals" in condition:
            values = condition["not_equals"]
            return values.get("left") != values.get("right")
        raise ValueError(f"Unsupported condition for step {step.id}")

    def _resolve(self, value: Any, session: Session) -> Any:
        if isinstance(value, dict):
            return {key: self._resolve(item, session) for key, item in value.items()}
        if isinstance(value, list):
            return [self._resolve(item, session) for item in value]
        if not isinstance(value, str):
            return value
        match = REFERENCE.match(value)
        if not match:
            return value
        output = session.plan.step(match.group(1)).output
        for part in (match.group(2) or "").split("."):
            if part:
                output = output[part] if isinstance(output, dict) else getattr(output, part)
        return output
