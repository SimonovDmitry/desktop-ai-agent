from urllib.parse import urlparse

from deskagent.actions.browser.base import DangerousBrowserAction
from deskagent.platform.common.browser.models import BrowserSecurityError
from deskagent.platform.common.browser.security import BrowserSecurityPolicy  # noqa: F401


class AcceptBrowserPermission(DangerousBrowserAction):
    name = "accept_browser_permission"
    description = "Grant a browser permission to an exact validated origin"
    parameters_schema = {
        "origin": {"type": "string", "required": True},
        "permission": {
            "type": "string", "required": True,
            "enum": ["geolocation", "notifications", "clipboardReadWrite", "audioCapture", "videoCapture"],
        },
        "tab_id": {"type": "string", "required": False},
        "browser": {"type": "string", "required": False},
    }

    def execute(self, context, parameters):
        manager = self.manager(context)
        try:
            origin = manager.policy.validate_url(parameters["origin"])
            parsed = urlparse(origin)
            exact_origin = f"{parsed.scheme}://{parsed.netloc}"
            browser_id, backend = manager._resolve(parameters.get("browser"))
            if not hasattr(backend, "browser_command"):
                raise BrowserSecurityError("Browser permission grants require a Chromium CDP backend")
            backend.browser_command(
                "Browser.grantPermissions",
                {"origin": exact_origin, "permissions": [parameters["permission"]]},
            )
            return self.success({
                "browser": browser_id,
                "origin": exact_origin,
                "permission": parameters["permission"],
                "granted": True,
            })
        except Exception as exc:
            return self.failure(exc)


class ClearBrowserData(DangerousBrowserAction):
    name = "clear_browser_data"
    description = "Clear selected site data for an exact origin"
    parameters_schema = {
        "origin": {"type": "string", "required": True},
        "data_types": {
            "type": "list", "required": False,
            "default": ["cookies", "local_storage", "indexeddb", "cache_storage"],
        },
        "browser": {"type": "string", "required": False},
    }

    DATA_TYPES = {
        "cookies": "cookies", "local_storage": "local_storage", "indexeddb": "indexeddb",
        "cache_storage": "cache_storage", "service_workers": "service_workers", "websql": "websql",
    }

    def execute(self, context, parameters):
        manager = self.manager(context)
        try:
            origin = manager.policy.validate_url(parameters["origin"])
            parsed = urlparse(origin)
            exact_origin = f"{parsed.scheme}://{parsed.netloc}"
            requested = parameters.get("data_types", list(self.DATA_TYPES)[:4])
            unknown = set(requested) - set(self.DATA_TYPES)
            if unknown:
                raise BrowserSecurityError(f"Unsupported browser data types: {', '.join(sorted(unknown))}")
            browser_id, backend = manager._resolve(parameters.get("browser"))
            if not hasattr(backend, "browser_command"):
                raise BrowserSecurityError("Clearing browser data requires a Chromium CDP backend")
            backend.browser_command(
                "Storage.clearDataForOrigin",
                {"origin": exact_origin, "storageTypes": ",".join(self.DATA_TYPES[item] for item in requested)},
            )
            return self.success({"browser": browser_id, "origin": exact_origin, "cleared": requested})
        except Exception as exc:
            return self.failure(exc)


class DeleteBrowserHistory(DangerousBrowserAction):
    name = "delete_browser_history"
    description = "Delete browser history when the connected semantic backend supports it"
    parameters_schema = {
        "browser": {"type": "string", "required": False},
        "since": {"type": "float", "required": False},
    }

    def execute(self, context, parameters):
        return self.failure(
            BrowserSecurityError(
                "History deletion is intentionally unavailable: stable CDP and Safari "
                "automation do not expose a scoped history API"
            )
        )
