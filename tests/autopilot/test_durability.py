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


def make_engine(tmp_path, policy=None):
    registry = ActionRegistry()
    for action in (Count, Camera, Parallel):
        registry.register(action)
    context = SimpleNamespace(
        logger=logging.getLogger("durability"), count=0,
        lock=threading.Lock(), active=0, max_active=0,
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
    assert recovered[retry.id].status is SessionStatus.READY
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
