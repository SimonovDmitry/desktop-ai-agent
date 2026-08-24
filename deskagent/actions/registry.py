class ActionRegistry:

    def __init__(self):
        self._actions = {}

    def register(self, action_class):
        self._actions[action_class.name] = action_class

    def create(self, name):
        if name not in self._actions:
            raise ValueError(
                f"Unknown action: {name}. "
                f"Available actions: {list(self._actions.keys())}"
            )

        return self._actions[name]