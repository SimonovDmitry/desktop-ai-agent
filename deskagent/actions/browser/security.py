from __future__ import annotations

import ipaddress
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

from deskagent.actions.browser.models import BrowserSecurityError
from deskagent.actions.browser.base import DangerousBrowserAction


class BrowserSecurityPolicy:
    """Validates browser inputs before they cross a browser automation boundary."""

    SAFE_SCHEMES = {"http", "https", "about"}
    BLOCKED_SCHEMES = {"data", "file", "javascript", "vbscript", "chrome", "edge", "devtools"}

    def __init__(
        self,
        allow_javascript: bool = False,
        javascript_origins: tuple[str, ...] = (),
        allow_private_networks: bool = False,
        allowed_download_dirs: tuple[str, ...] = ("~/Downloads",),
        allowed_upload_paths: tuple[str, ...] = (),
    ):
        self.allow_javascript = allow_javascript
        self.javascript_origins = tuple(origin.rstrip("/") for origin in javascript_origins)
        self.allow_private_networks = allow_private_networks
        self.allowed_download_dirs = self._expand_paths(allowed_download_dirs)
        self.allowed_upload_paths = self._expand_paths(allowed_upload_paths)

    @classmethod
    def from_settings(cls, settings):
        browser = getattr(settings, "browser", None)
        security = getattr(settings, "security", None)
        return cls(
            allow_javascript=getattr(browser, "allow_javascript", False),
            javascript_origins=tuple(getattr(browser, "javascript_allowed_origins", ())),
            allow_private_networks=getattr(browser, "allow_private_networks", False),
            allowed_download_dirs=tuple(getattr(browser, "allowed_download_dirs", ("~/Downloads",))),
            allowed_upload_paths=tuple(getattr(security, "allowed_paths", ())),
        )

    def validate_url(self, url: str, *, allow_internal: bool = False) -> str:
        if not isinstance(url, str) or not url.strip():
            raise BrowserSecurityError("URL must be a non-empty string")
        value = url.strip()
        parsed = urlparse(value)
        if not parsed.scheme:
            value = "https://" + value
            parsed = urlparse(value)
        scheme = parsed.scheme.lower()
        if scheme in self.BLOCKED_SCHEMES or scheme not in self.SAFE_SCHEMES:
            raise BrowserSecurityError(f"URL scheme is not allowed: {scheme}")
        if scheme == "about":
            if allow_internal and value in {"about:blank", "about:newtab"}:
                return value
            raise BrowserSecurityError("Internal browser URLs are blocked")
        if parsed.username or parsed.password:
            raise BrowserSecurityError("Credentials embedded in URLs are blocked")
        if not parsed.hostname:
            raise BrowserSecurityError("URL must include a hostname")
        self._validate_host(parsed.hostname)
        return value

    def validate_javascript(self, source: str, page_url: str) -> str:
        if not self.allow_javascript:
            raise BrowserSecurityError("Page JavaScript execution is disabled")
        parsed = urlparse(page_url)
        origin = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        if not self.javascript_origins or origin not in self.javascript_origins:
            raise BrowserSecurityError(f"JavaScript execution is not allowlisted for origin: {origin}")
        if not isinstance(source, str) or not source.strip():
            raise BrowserSecurityError("JavaScript source must be non-empty")
        return source

    def validate_download_path(self, path: str | None) -> Path:
        target = Path(path or "~/Downloads").expanduser().resolve()
        if not any(self._within(target, root) for root in self.allowed_download_dirs):
            raise BrowserSecurityError(f"Download directory is outside the allowlist: {target}")
        target.mkdir(parents=True, exist_ok=True)
        return target

    def validate_upload_path(self, path: str) -> Path:
        target = Path(path).expanduser().resolve()
        if not target.is_file():
            raise BrowserSecurityError(f"Upload file does not exist: {target}")
        if not self.allowed_upload_paths or not any(
            self._within(target, root) for root in self.allowed_upload_paths
        ):
            raise BrowserSecurityError(f"Upload path is outside the allowlist: {target}")
        return target

    def _validate_host(self, host: str):
        lowered = host.lower().rstrip(".")
        if lowered in {"localhost", "localhost.localdomain"} and not self.allow_private_networks:
            raise BrowserSecurityError("Local network navigation is disabled")
        try:
            address = ipaddress.ip_address(lowered)
        except ValueError:
            if self.allow_private_networks:
                return
            try:
                addresses = {item[4][0] for item in socket.getaddrinfo(lowered, None)}
            except socket.gaierror as exc:
                raise BrowserSecurityError(f"URL hostname cannot be resolved: {host}") from exc
            for value in addresses:
                self._validate_ip(ipaddress.ip_address(value))
            return
        self._validate_ip(address)

    def _validate_ip(self, address):
        if not self.allow_private_networks and (
            address.is_private or address.is_loopback or address.is_link_local or address.is_reserved
        ):
            raise BrowserSecurityError("Private and local network navigation is disabled")

    @staticmethod
    def _expand_paths(paths):
        return tuple(Path(os.path.expandvars(path)).expanduser().resolve() for path in paths)

    @staticmethod
    def _within(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False


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
