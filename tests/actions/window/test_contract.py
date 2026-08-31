import inspect

import pytest

from deskagent.actions.types import ActionCategory, RiskLevel
from deskagent.actions.window import appearance, arrangement, display, focus, groups, hierarchy, information, lifecycle, position, size, state

MODULES = [appearance, arrangement, display, focus, groups, hierarchy, information, lifecycle, position, size, state]


def concrete_actions(module):
    # Both deskagent.actions.base.Action and deskagent.core.action.Action are used
    # by the supplied sources, so discover their common concrete descendants by
    # looking for classes defined directly in the module.
    return [
        cls for _, cls in inspect.getmembers(module, inspect.isclass)
        if cls.__module__ == module.__name__ and hasattr(cls, "execute") and hasattr(cls, "name")
    ]


@pytest.mark.parametrize("module", MODULES, ids=lambda m: m.__name__.rsplit('.', 1)[-1])
def test_module_contains_concrete_actions(module):
    assert concrete_actions(module), f"No actions found in {module.__name__}"


@pytest.mark.parametrize("module", MODULES, ids=lambda m: m.__name__.rsplit('.', 1)[-1])
def test_action_names_are_unique_within_module(module):
    actions = concrete_actions(module)
    names = [cls.name for cls in actions]
    assert len(names) == len(set(names))
    assert all(isinstance(name, str) and name for name in names)


@pytest.mark.parametrize("module", MODULES, ids=lambda m: m.__name__.rsplit('.', 1)[-1])
def test_action_metadata_and_schema(module):
    for cls in concrete_actions(module):
        action = cls()
        assert isinstance(action.name, str) and action.name
        assert isinstance(action.description, str) and action.description
        assert action.category is ActionCategory.APPLICATION
        assert isinstance(action.risk_level, RiskLevel)
        assert isinstance(action.requires_confirmation, bool)
        assert isinstance(action.reversible, bool)
        assert isinstance(action.parameters_schema, dict)

        for parameter, spec in action.parameters_schema.items():
            assert isinstance(parameter, str) and parameter
            assert isinstance(spec, dict)
            assert isinstance(spec.get("type"), str) and spec["type"]
            if "required" in spec:
                assert isinstance(spec["required"], bool)
            if "enum" in spec:
                assert isinstance(spec["enum"], (list, tuple))
                assert spec["enum"]


@pytest.mark.parametrize("module", MODULES, ids=lambda m: m.__name__.rsplit('.', 1)[-1])
def test_required_window_actions_have_window_id_schema(module):
    for cls in concrete_actions(module):
        schema = cls().parameters_schema
        if "window_id" in schema:
            spec = schema["window_id"]
            assert spec["type"] == "integer"
            assert spec.get("required") is True
