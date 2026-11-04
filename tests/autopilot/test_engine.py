import logging
from types import SimpleNamespace

import pytest

from deskagent.actions.base import Action, ActionRegistry
from deskagent.actions.executor import ActionExecutor
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel
from deskagent.agent.capabilities.tools import ActionToolCatalog
from deskagent.autopilot import (
    AutopilotEngine,
    AutopilotMode,
    Plan,
    RetryPolicy,
    SessionStatus,
    SessionStore,
    Step,
    StepStatus,
)
from deskagent.autopilot.models import utc_now
from deskagent.autopilot.validation import PlanValidationError


class Produce(Action):
    name = "produce"
    description = "Produce a value"
    category = ActionCategory.PRODUCTIVITY
    parameters_schema = {"value": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        context.calls.append((self.name, parameters))
        return ActionResult(True, {"value": parameters["value"]})


class Consume(Action):
    name = "consume"
    description = "Consume a value"
    category = ActionCategory.PRODUCTIVITY
    parameters_schema = {"value": {"type": "integer", "required": True}}

    def execute(self, context, parameters):
        context.calls.append((self.name, parameters))
        return ActionResult(True, {"consumed": parameters["value"]})


class Flaky(Action):
    name = "flaky"
    description = "Fail once"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        context.flaky_calls += 1
        if context.flaky_calls == 1:
            return ActionResult(False, error="not ready", error_code="TEMPORARY_UNAVAILABLE")
        return ActionResult(True, {"ready": True})


class Dangerous(Action):
    name = "dangerous"
    description = "Dangerous action"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    parameters_schema = {}

    def execute(self, context, parameters):
        context.calls.append((self.name, parameters))
        return ActionResult(True)


@pytest.fixture
def runtime(tmp_path):
    registry = ActionRegistry()
    for action in (Produce, Consume, Flaky, Dangerous):
        registry.register(action)
    context = SimpleNamespace(logger=logging.getLogger("autopilot-test"), calls=[], flaky_calls=0)
    executor = ActionExecutor(registry, confirmation_handler=lambda *_: True)
    catalog = ActionToolCatalog(registry, executor, context)
    store = SessionStore(tmp_path / "sessions.sqlite")
    engine = AutopilotEngine(catalog, store, sleep=lambda _: None)
    yield engine, store, context
    store.close()


def test_executes_dependencies_and_resolves_outputs(runtime):
    engine, store, context = runtime
    plan = Plan(
        [
            Step("first", "Produce", "produce", {"value": 7}),
            Step(
                "second",
                "Consume",
                "consume",
                {"value": "${steps.first.output.value}"},
                depends_on=("first",),
            ),
        ]
    )

    session = engine.create_session("pipeline", plan, AutopilotMode.AUTOPILOT)
    result = engine.start(session.id)

    assert result.status is SessionStatus.COMPLETED
    assert [step.status for step in result.plan.steps] == [StepStatus.SUCCEEDED, StepStatus.SUCCEEDED]
    assert context.calls == [("produce", {"value": 7}), ("consume", {"value": 7})]
    assert [event["event"] for event in store.events(session.id)][-1] == "session_completed"


def test_retries_only_explicitly_idempotent_steps(runtime):
    engine, _, context = runtime
    retry = RetryPolicy(max_attempts=2, initial_delay_seconds=0, retry_on=("TEMPORARY_UNAVAILABLE",))
    session = engine.create_session(
        "retry", Plan([Step("flaky", "Flaky", "flaky", retry=retry, idempotent=True)])
    )

    result = engine.start(session.id)

    assert result.status is SessionStatus.COMPLETED
    assert result.plan.step("flaky").attempts == 2
    assert context.flaky_calls == 2


def test_sensitive_step_waits_for_durable_confirmation(runtime):
    engine, store, context = runtime
    session = engine.create_session("danger", Plan([Step("danger", "Danger", "dangerous")]))

    pending = engine.start(session.id)
    reloaded = store.get(session.id)

    assert pending.status is SessionStatus.WAITING_FOR_USER
    assert reloaded.pending_confirmation["step_id"] == "danger"
    assert context.calls == []
    completed = engine.approve(session.id, True)
    assert completed.status is SessionStatus.COMPLETED
    assert context.calls == [("dangerous", {})]


def test_recovery_does_not_repeat_uncertain_non_idempotent_action(runtime):
    engine, store, _ = runtime
    session = engine.create_session("recover", Plan([Step("write", "Write", "produce", {"value": 1})]))
    session.status = SessionStatus.RUNNING
    session.current_step_id = "write"
    session.plan.step("write").status = StepStatus.RUNNING
    store.save(session, "step_started", "write")

    recovered = engine.recover_incomplete()[0]

    assert recovered.status is SessionStatus.WAITING_FOR_USER
    assert recovered.plan.step("write").status is StepStatus.WAITING_FOR_USER
    assert recovered.pending_confirmation["kind"] == "uncertain_result"


def test_plan_validator_rejects_cycles(runtime):
    engine, _, _ = runtime
    plan = Plan(
        [
            Step("a", "A", "produce", {"value": 1}, depends_on=("b",)),
            Step("b", "B", "produce", {"value": 2}, depends_on=("a",)),
        ]
    )
    with pytest.raises(PlanValidationError, match="dependency cycle"):
        engine.validator.validate(plan)


def test_store_redacts_secrets_in_events(runtime):
    engine, store, _ = runtime
    session = engine.create_session("redaction", Plan([Step("one", "One", "produce", {"value": 1})]))
    store.save(session, "custom", payload={"api_key": "secret"})
    assert store.events(session.id)[-1]["payload"]["api_key"] == "***REDACTED***"


def test_cancel_marks_unfinished_steps(runtime):
    engine, _, _ = runtime
    session = engine.create_session("cancel", Plan([Step("one", "One", "produce", {"value": 1})]))
    cancelled = engine.cancel(session.id)
    assert cancelled.status is SessionStatus.CANCELLED
    assert cancelled.plan.step("one").status is StepStatus.CANCELLED


def test_revise_plan_preserves_completed_steps(runtime):
    engine, store, _ = runtime
    session = engine.create_session("revise", Plan([Step("one", "One", "produce", {"value": 1})]))
    session.plan.step("one").status = StepStatus.SUCCEEDED
    session.plan.step("one").output = {"value": 1}
    session.status = SessionStatus.FAILED
    session.updated_at = utc_now()
    store.save(session)
    revised = engine.revise_plan(
        session.id,
        Plan(
            [
                Step("one", "One", "produce", {"value": 1}),
                Step("two", "Two", "consume", {"value": 1}, depends_on=("one",)),
            ]
        ),
        "add missing step",
    )
    assert revised.plan.version == 2
    assert revised.plan.step("one").status is StepStatus.SUCCEEDED
