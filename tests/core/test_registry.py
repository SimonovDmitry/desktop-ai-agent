import pytest

from deskagent.actions.base import Action
from deskagent.actions.registry import ActionRegistry
from deskagent.actions.result import ActionResult
from deskagent.actions.types import ActionCategory, RiskLevel


class DummyAction(Action):
    name = "dummy"
    description = "Dummy action"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    parameters_schema = {}

    def execute(self, context, parameters):
        return ActionResult(success=True, data={"ok": True})


def test_registry_registers_action():
    registry = ActionRegistry()
    registry.register(DummyAction)
    assert registry._actions["dummy"] is DummyAction


def test_registry_create_returns_registered_action():
    registry = ActionRegistry()
    registry.register(DummyAction)
    result = registry.create("dummy")
    assert isinstance(result, DummyAction)


def test_registry_create_unknown_action_raises():
    registry = ActionRegistry()
    with pytest.raises(ValueError, match="Unknown action"):
        registry.create("missing")


def test_registry_can_register_multiple_actions():
    class AnotherAction(DummyAction):
        name = "another"

    registry = ActionRegistry()
    registry.register(DummyAction)
    registry.register(AnotherAction)

    assert set(registry._actions) == {"dummy", "another"}
