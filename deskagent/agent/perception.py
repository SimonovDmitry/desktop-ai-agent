from typing import Any, Callable


class ContextCollector:
    def __init__(self, context, screen_provider: Callable | None = None):
        self.context = context
        self.screen_provider = screen_provider

    def collect(self) -> tuple[dict[str, Any], dict[str, Any]]:
        return self.screen(), self.system()

    def screen(self) -> dict[str, Any]:
        data = {
            "application": self._call("application.information.get_active"),
            "window": self._call("window.information.get_active_window"),
        }
        if self.screen_provider:
            data.update(self.screen_provider() or {})
        return {key: value for key, value in data.items() if value is not None}

    def system(self) -> dict[str, Any]:
        battery = self._call("system.information.get_battery_status")
        return {"battery": battery} if battery is not None else {}

    def _call(self, path):
        try:
            value = self.context.services
            for name in path.split("."):
                value = getattr(value, name)
            return value()
        except Exception:
            return None
