from abc import ABC, abstractmethod

from deskagent.core.context import ActionContext
from deskagent.actions.result import ActionResult
from deskagent.actions.types import RiskLevel, ActionCategory


class Action(ABC):
    name: str
    description: str
    category: ActionCategory
    risk_level: RiskLevel
    requires_confirmation: bool = False
    reversible: bool = False
    parameters_schema: dict = {}

    @abstractmethod
    def execute(self, context: ActionContext, parameters: dict) -> ActionResult:
        pass
