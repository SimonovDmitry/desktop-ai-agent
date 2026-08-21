from abc import ABC, abstractmethod

from abc import ABC, abstractmethod

from deskagent.actions.context import ActionContext
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class Action(ABC):
    name: str
    description: str
    category: ActionCategory
    risk_level: RiskLevel
    requires_confirmation: bool = False
    reversible: bool = True

    @abstractmethod
    def execute(self, context: ActionContext) -> ActionResult:
        pass

    def __init__(self, logger):
        self._logger = logger

    @classmethod
    def create(self, action_name, logger):
        if action_name not in self._METHODS:
                raise ValueError(f"This action is not defined. Available actions: {self._METHODS.keys()}")

        return Action._METHODS[action_name](self, logger)

    @abstractmethod
    def execute(self, config):
        pass
