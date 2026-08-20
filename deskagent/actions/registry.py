
class ActionRegistry:
    _ACTIONS = dict()

    def __init__(self):
        pass

    def register(self, name, action_class):
        self._ACTIONS[name] = action_class

    def create(self, name, logger):
        if name not in self._ACTIONS:
            raise ValueError(
                f"Unknown action: {name}. "
                f"Available actions: {list(self._ACTIONS.keys())}"
            )

        return self._ACTIONS[name](logger)