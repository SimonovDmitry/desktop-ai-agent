from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Size:
    width: float
    height: float


@dataclass(frozen=True)
class Bounds:
    position: Point
    size: Size

    @property
    def visible(self) -> bool:
        return self.size.width > 0 and self.size.height > 0


@dataclass
class UIElement:
    id: str
    role: str
    subrole: str | None = None
    title: str | None = None
    value: Any = None
    description: str | None = None
    position: Point | None = None
    size: Size | None = None
    enabled: bool = True
    focused: bool = False
    selected: bool = False
    actions: list[str] = field(default_factory=list)
    children: list[UIElement] = field(default_factory=list)
    application: str | None = None
    application_pid: int | None = None
    window: str | None = None
    locator: str = ""
    path: tuple[int, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def bounds(self) -> Bounds | None:
        if self.position is None or self.size is None:
            return None
        return Bounds(self.position, self.size)

    @property
    def visible(self) -> bool:
        return bool(
            self.bounds
            and self.bounds.visible
            and not self.attributes.get("hidden", False)
        )


@dataclass(frozen=True)
class ElementQuery:
    application: str | None = None
    window: str | None = None
    role: str | None = None
    text: str | None = None
    locator: str | None = None
    visible_only: bool = False
    enabled_only: bool = False
    fuzzy: bool = False
    minimum_confidence: float = 0.6


@dataclass(frozen=True)
class UIElementMatch:
    element: UIElement
    confidence: float
    exact: bool
    matched_field: str | None = None


class AccessibilityError(RuntimeError):
    """Base error raised by the accessibility subsystem."""


class AccessibilityPermissionError(AccessibilityError):
    """Raised when macOS Accessibility permission is unavailable."""


class ElementNotFoundError(AccessibilityError):
    """Raised when a requested UI element cannot be resolved."""


class UnsupportedAccessibilityError(AccessibilityError):
    """Raised when accessibility is used on an unsupported platform."""
