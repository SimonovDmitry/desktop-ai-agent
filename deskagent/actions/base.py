from abc import ABC, abstractmethod
from typing import Type

from deskagent.core.context import ActionContext
from deskagent.actions.types import RiskLevel, ActionCategory, ActionResult


class Action(ABC):
    name: str
    description: str
    category: ActionCategory
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False
    reversible: bool = False
    required_permissions: tuple[str, ...] = ()
    discoverable: bool = True
    parameters_schema: dict = {}

    @abstractmethod
    def execute(self, context: ActionContext, parameters: dict) -> ActionResult:
        pass


class ActionRegistry:
    def __init__(self):
        self._actions: dict[str, Type[Action]] = {}

    def register(self, action_class: Type[Action]) -> None:
        if not issubclass(action_class, Action):
            raise TypeError(
                f"{action_class.__name__} must inherit from Action"
            )

        name = action_class.name

        if not name:
            raise ValueError(
                f"{action_class.__name__} must define 'name'"
            )

        if name in self._actions:
            current = self._actions[name]
            raise ValueError(
                f"Action already registered: {name} "
                f"({current.__module__}.{current.__name__} and "
                f"{action_class.__module__}.{action_class.__name__})"
            )

        self._actions[name] = action_class

    def get(self, name: str) -> Type[Action]:
        try:
            return self._actions[name]
        except KeyError:
            raise ValueError(
                f"Unknown action: {name}. "
                f"Available actions: {list(self._actions.keys())}"
            )

    def create(self, name: str) -> Action:
        action_class = self.get(name)
        return action_class()

    def contains(self, name: str) -> bool:
        return name in self._actions

    def names(self) -> list[str]:
        return list(self._actions.keys())

    def all(self) -> list[Type[Action]]:
        return list(self._actions.values())

    def count(self) -> int:
        return len(self._actions)
