from __future__ import annotations

from abc import ABC, abstractmethod

from deskagent.actions.base import Action
from deskagent.actions.browser.models import BrowserError
from deskagent.actions.types import ActionCategory, ActionResult, RiskLevel


class BrowserBackend(ABC):
    @abstractmethod
    def available(self) -> bool:
        pass

    @abstractmethod
    def list_tabs(self):
        pass

    @abstractmethod
    def command(self, method: str, params: dict | None = None, tab_id: str | None = None):
        pass


class BrowserAction(Action):
    category = ActionCategory.BROWSER
    risk_level = RiskLevel.LOW

    @staticmethod
    def manager(context):
        manager = getattr(context.services, "browser", None)
        if manager is None:
            raise RuntimeError("Browser service is not configured")
        manager.configure(getattr(context, "settings", None))
        return manager

    @staticmethod
    def success(data=None, **values):
        if values:
            data = {**(data if isinstance(data, dict) else {}), **values}
        return ActionResult(success=True, data=data)

    @staticmethod
    def failure(exc):
        code = getattr(exc, "code", None)
        if code is None:
            code = "TIMEOUT" if isinstance(exc, TimeoutError) else "BROWSER_ERROR"
        return ActionResult(success=False, error=str(exc), error_code=code)

    def run(self, context, operation, *args, **kwargs):
        try:
            return self.success(operation(*args, **kwargs))
        except Exception as exc:
            return self.failure(exc)


class DangerousBrowserAction(BrowserAction):
    risk_level = RiskLevel.HIGH
    requires_confirmation = True


def browser_error(message: str, code: str = "BROWSER_ERROR"):
    error = BrowserError(message)
    error.code = code
    return error


class ListBrowsers(BrowserAction):
    name = "list_browsers"
    description = "List supported installed browsers and semantic automation backends"
    parameters_schema = {}

    def execute(self, context, parameters):
        return self.run(
            context,
            lambda: {"browsers": [item.to_dict() for item in self.manager(context).list_browsers()]},
        )


class GetDefaultBrowser(BrowserAction):
    name = "get_default_browser"
    description = "Get the configured or operating-system default web browser"
    parameters_schema = {}

    def execute(self, context, parameters):
        return self.run(context, lambda: self.manager(context).default_browser().to_dict())


class LaunchBrowser(BrowserAction):
    name = "launch_browser"
    description = "Launch a browser with a semantic automation endpoint"
    parameters_schema = {
        "browser": {"type": "string", "required": False},
        "url": {"type": "string", "required": False},
        "incognito": {"type": "boolean", "required": False, "default": False},
        "headless": {"type": "boolean", "required": False, "default": False},
    }

    def execute(self, context, parameters):
        params = parameters or {}
        return self.run(
            context, self.manager(context).launch, params.get("browser"), params.get("url"),
            params.get("incognito", False), params.get("headless", False),
        )


class GetBrowserStatus(BrowserAction):
    name = "get_browser_status"
    description = "Get browser installation, process, backend, and tab status"
    parameters_schema = {"browser": {"type": "string", "required": False}}

    def execute(self, context, parameters):
        return self.run(context, self.manager(context).status, (parameters or {}).get("browser"))


class GetActiveBrowser(BrowserAction):
    name = "get_active_browser"
    description = "Get the active browser that has an available semantic backend"
    parameters_schema = {}

    def execute(self, context, parameters):
        def operation():
            browser = self.manager(context).active_browser()
            return browser.to_dict() if browser else None
        return self.run(context, operation)
