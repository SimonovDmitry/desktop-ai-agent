import inspect

import pytest

from deskagent.actions.base import Action
from deskagent.actions.types import ActionCategory, RiskLevel


def test_action_is_abstract():
    assert inspect.isabstract(Action)


def test_minimal_action_implementation_can_be_instantiated():
    class ExampleAction(Action):
        name = "example"
        description = "Example"
        category = ActionCategory.SYSTEM
        risk_level = RiskLevel.LOW
        parameters_schema = {}

        def execute(self, context, parameters):
            return None

    action = ExampleAction()
    assert action.name == "example"
    assert action.requires_confirmation is False
    assert action.reversible is False


def test_action_default_flags_are_safe():
    class ExampleAction(Action):
        name = "example"
        description = "Example"
        category = ActionCategory.SYSTEM
        risk_level = RiskLevel.LOW

        def execute(self, context, parameters):
            return None

    action = ExampleAction()
    assert action.requires_confirmation is False
    assert action.reversible is False
