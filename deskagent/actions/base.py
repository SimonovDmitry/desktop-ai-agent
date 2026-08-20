from abc import ABC, abstractmethod

class Action(ABC):
    _ACTIONS = dict()

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


