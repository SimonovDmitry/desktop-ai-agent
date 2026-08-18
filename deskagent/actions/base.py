from abc import ABC, abstractmethod

class Action(ABC):
    _METHODS = dict()

    def __init__(self):
        pass

    def __init_subclass__(cls):
        pass

    def create(self, action_name, logger):
        if action_name not in self._METHODS:
                raise ValueError(f"This action is not defined. Available actions: {self._METHODS.keys()}")

        return Action._METHODS[action_name](self, logger)

    @abstractmethod
    def execute(self):
        pass


