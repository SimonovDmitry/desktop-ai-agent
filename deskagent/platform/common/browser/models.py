from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class BrowserKind(str, Enum):
    CHROME = "chrome"
    EDGE = "edge"
    CHROMIUM = "chromium"
    SAFARI = "safari"


class BackendKind(str, Enum):
    CDP = "cdp"
    SAFARI = "safari"


@dataclass(slots=True)
class BrowserInfo:
    id: str
    name: str
    kind: BrowserKind
    application: str
    installed: bool = False
    running: bool = False
    backend: BackendKind | None = None
    debug_port: int | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["kind"] = self.kind.value
        value["backend"] = self.backend.value if self.backend else None
        return value


@dataclass(slots=True)
class BrowserTab:
    id: str
    title: str = ""
    url: str = ""
    active: bool = False
    pinned: bool = False
    browser: str = ""
    backend: BackendKind = BackendKind.CDP
    websocket_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["backend"] = self.backend.value
        value.pop("websocket_url", None)
        return value


@dataclass(slots=True)
class DownloadItem:
    id: str
    url: str
    filename: str | None = None
    path: str | None = None
    state: str = "in_progress"
    received_bytes: int = 0
    total_bytes: int | None = None
    error: str | None = None
    started_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PageMetadata:
    url: str
    title: str
    description: str | None = None
    canonical_url: str | None = None
    language: str | None = None
    charset: str | None = None
    content_type: str | None = None
    viewport: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BrowserError(RuntimeError):
    code = "BROWSER_ERROR"


class BrowserUnavailableError(BrowserError):
    code = "BROWSER_UNAVAILABLE"


class BrowserConnectionError(BrowserError):
    code = "BROWSER_CONNECTION_ERROR"


class BrowserTimeoutError(BrowserError, TimeoutError):
    code = "TIMEOUT"


class BrowserSecurityError(BrowserError):
    code = "SECURITY_BLOCKED"


class BrowserNotSupportedError(BrowserError):
    code = "NOT_SUPPORTED"


class BrowserTargetError(BrowserError):
    code = "TAB_NOT_FOUND"
