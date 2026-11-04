import logging
import threading
import time
from types import SimpleNamespace

from deskagent.actions.base import Action, ActionRegistry
from deskagent.actions.executor import ActionExecutor
from deskagent.actions.types import ActionCategory, ActionResult
from deskagent.agent.capabilities.policy import ActionPolicy, PolicyConfig
from deskagent.agent.capabilities.tools import ActionToolCatalog
from deskagent.autopilot import AutopilotEngine, Plan, SessionStatus, SessionStore, Step, StepStatus
from deskagent.autopilot.models import Compensation, Verification, VerificationType


class Count(Action):
    name = "count"
    description = "Count execution"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        context.count += 1
        return ActionResult(True, {"count": context.count})


class Camera(Action):
    name = "camera_capture"
    description = "Capture camera"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        context.count += 1
        return ActionResult(True)


class Parallel(Action):
    name = "parallel"
    description = "Track parallelism"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        with context.lock:
            context.active += 1
            context.max_active = max(context.max_active, context.active)
        time.sleep(0.03)
        with context.lock:
            context.active -= 1
        return ActionResult(True)


class Undo(Action):
    name = "undo"
    description = "Undo count"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        context.count -= 1
        return ActionResult(True)


class Slow(Action):
    name = "slow"
    description = "Slow action"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        time.sleep(0.05)
        return ActionResult(True)


class Cancellable(Action):
    name = "cancellable"
    description = "Cancellable action"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        self.context = context
        context.started.set()
        context.cancelled.wait(1)
        return ActionResult(False, error="cancelled", error_code="ACTION_CANCELLED")

    def cancel(self):
        self.context.cancelled.set()


class PauseSelf(Action):
    name = "pause_self"
    description = "Pause its own session"
    category = ActionCategory.SYSTEM
    parameters_schema = {}

    def execute(self, context, parameters):
        context.engine.pause(context.session_id)
        return ActionResult(True)


def make_engine(tmp_path, policy=None):
    registry = ActionRegistry()
    for action in (Count, Camera, Parallel, Undo, Slow, Cancellable, PauseSelf):
        registry.register(action)
    context = SimpleNamespace(
        logger=logging.getLogger("durability"), count=0,
        lock=threading.Lock(), active=0, max_active=0,
        started=threading.Event(), cancelled=threading.Event(),
    )
    catalog = ActionToolCatalog(
        registry, ActionExecutor(registry, confirmation_handler=lambda *_: True),
        context, policy=policy,
    )
    store = SessionStore(tmp_path / "durable.sqlite")
    return AutopilotEngine(catalog, store, max_parallelism=4), store, context


def test_recovery_handles_verifying_retry_and_cancelling(tmp_path):
    engine, store, _ = make_engine(tmp_path)
    verifying = engine.create_session("verify", Plan([Step("s", "S", "count")]))
    verifying.status = SessionStatus.RUNNING
    verifying.plan.step("s").status = StepStatus.VERIFYING
    store.save(verifying)
    retry = engine.create_session("retry", Plan([Step("s", "S", "count", idempotent=True)]))
    retry.status = SessionStatus.RUNNING
    retry.plan.step("s").status = StepStatus.RETRY_SCHEDULED
    retry.plan.step("s").retry_at = "2999-01-01T00:00:00+00:00"
    store.save(retry)
    cancelling = engine.create_session("cancel", Plan([Step("s", "S", "count")]))
    cancelling.status = SessionStatus.CANCELLING
    store.save(cancelling)

    recovered = {item.id: item for item in engine.recover_incomplete()}

    assert recovered[verifying.id].status is SessionStatus.WAITING_FOR_USER
    assert recovered[retry.id].status is SessionStatus.RUNNING
    assert recovered[retry.id].plan.step("s").status is StepStatus.RETRY_SCHEDULED
    assert recovered[cancelling.id].status is SessionStatus.CANCELLED


def test_critical_confirmation_requires_exact_phrase(tmp_path):
    engine, store, context = make_engine(tmp_path)
    first = engine.create_session("camera", Plan([Step("camera", "Camera", "camera_capture")]))
    pending = engine.start(first.id)
    assert pending.pending_confirmation["requires_explicit_text"] is True
    denied = engine.approve(first.id, True)
    assert denied.status is SessionStatus.CANCELLED
    assert context.count == 0

    second = engine.create_session("camera", Plan([Step("camera", "Camera", "camera_capture")]))
    pending = engine.start(second.id)
    approved = engine.approve(
        second.id,
        {
            "approved": True,
            "confirmation_id": pending.pending_confirmation["confirmation_id"],
            "text": pending.pending_confirmation["required_phrase"],
        },
    )
    assert approved.status is SessionStatus.COMPLETED
    assert context.count == 1
    store.close()


def test_dry_run_and_action_limit_are_enforced(tmp_path):
    dry_engine, dry_store, context = make_engine(tmp_path, ActionPolicy(PolicyConfig(dry_run=True)))
    session = dry_engine.create_session("dry", Plan([Step("one", "One", "count")]))
    result = dry_engine.start(session.id)
    assert result.status is SessionStatus.COMPLETED
    assert result.plan.step("one").output["dry_run"] is True
    assert context.count == 0
    dry_store.close()

    limited_engine, limited_store, context = make_engine(
        tmp_path / "limited", ActionPolicy(PolicyConfig(max_actions=1))
    )
    session = limited_engine.create_session(
        "limited",
        Plan([
            Step("one", "One", "count", resources=("one",)),
            Step("two", "Two", "count", depends_on=("one",), resources=("two",)),
        ]),
    )
    result = limited_engine.start(session.id)
    assert result.status is SessionStatus.FAILED
    assert result.plan.step("two").error_code == "ACTION_LIMIT"
    assert context.count == 1
    limited_store.close()


def test_independent_resources_execute_in_parallel(tmp_path):
    engine, store, context = make_engine(tmp_path)
    session = engine.create_session(
        "parallel",
        Plan([
            Step("one", "One", "parallel", resources=("resource:one",)),
            Step("two", "Two", "parallel", resources=("resource:two",)),
        ]),
    )
    result = engine.start(session.id)
    assert result.status is SessionStatus.COMPLETED
    assert context.max_active == 2
    store.close()


def test_plan_revision_reason_is_not_overwritten(tmp_path):
    engine, store, _ = make_engine(tmp_path)
    session = engine.create_session("plan", Plan([Step("one", "One", "count")]))
    engine.revise_plan(session.id, Plan([Step("two", "Two", "count")]), "new approach")
    row = store._connection.execute(
        "SELECT reason FROM plan_versions WHERE session_id=? AND version=2", (session.id,)
    ).fetchone()
    assert row["reason"] == "new approach"
    store.close()


def test_timeout_and_declarative_verification(tmp_path):
    engine, store, _ = make_engine(tmp_path)
    timed = engine.create_session(
        "timeout", Plan([Step("slow", "Slow", "slow", timeout_seconds=0.001)])
    )
    assert engine.start(timed.id).plan.step("slow").error_code == "TIMEOUT"

    checked = engine.create_session(
        "verify",
        Plan([Step(
            "count", "Count", "count",
            verifications=(Verification(
                VerificationType.OUTPUT_EQUALS,
                {"path": "count", "expected": 999},
            ),),
        )]),
    )
    result = engine.start(checked.id)
    assert result.status is SessionStatus.FAILED
    assert result.plan.step("count").error_code == "VERIFICATION_FAILED"
    store.close()


def test_compensation_requires_confirmation_and_runs_in_reverse(tmp_path):
    engine, store, context = make_engine(tmp_path)
    session = engine.create_session(
        "compensate",
        Plan([Step("count", "Count", "count", compensation=Compensation("undo"))]),
    )
    completed = engine.start(session.id)
    assert completed.status is SessionStatus.COMPLETED
    pending = engine.cancel(session.id, compensate=True)
    assert pending.status is SessionStatus.WAITING_FOR_USER
    result = engine.approve(session.id, True)
    assert result.status is SessionStatus.CANCELLED
    assert context.count == 0
    store.close()


def test_cancel_propagates_to_active_cancellable_action(tmp_path):
    engine, store, context = make_engine(tmp_path)
    session = engine.create_session(
        "cancel running", Plan([Step("active", "Active", "cancellable")])
    )
    thread = threading.Thread(target=engine.start, args=(session.id,))
    thread.start()
    assert context.started.wait(1)
    cancelled = engine.cancel(session.id)
    thread.join(1)
    assert cancelled.status is SessionStatus.CANCELLED
    assert context.cancelled.is_set()
    assert store.get(session.id).status is SessionStatus.CANCELLED
    store.close()


def test_pause_is_observed_during_active_execution(tmp_path):
    engine, store, context = make_engine(tmp_path)
    session = engine.create_session(
        "pause running",
        Plan([
            Step("pause", "Pause", "pause_self"),
            Step("after", "After", "count", depends_on=("pause",)),
        ]),
    )
    context.engine, context.session_id = engine, session.id
    paused = engine.start(session.id)
    assert paused.status is SessionStatus.PAUSED
    assert paused.plan.step("pause").status is StepStatus.SUCCEEDED
    assert paused.plan.step("after").status is StepStatus.BLOCKED
    completed = engine.resume(session.id)
    assert completed.status is SessionStatus.COMPLETED
    store.close()
