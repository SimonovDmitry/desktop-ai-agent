from __future__ import annotations

import hashlib
from deskagent.platform.macos.accessibility_backend import MacOSAXBackend
from dataclasses import replace
from typing import Any

from deskagent.platform.common.accessibility.locator import ElementLocator, normalize_text
from deskagent.platform.common.accessibility.models import (
    AccessibilityError,
    AccessibilityPermissionError,
    ElementNotFoundError,
    ElementQuery,
    UIElement,
    UIElementMatch,
)
from deskagent.platform.macos.accessibility_permissions import (
    get_accessibility_status,
    request_accessibility_permission,
)

ATTRIBUTES = {
    "role": "AXRole",
    "subrole": "AXSubrole",
    "title": "AXTitle",
    "value": "AXValue",
    "description": "AXDescription",
    "position": "AXPosition",
    "size": "AXSize",
    "enabled": "AXEnabled",
    "focused": "AXFocused",
    "selected": "AXSelected",
    "children": "AXChildren",
    "windows": "AXWindows",
    "focused_window": "AXFocusedWindow",
    "focused_element": "AXFocusedUIElement",
    "identifier": "AXIdentifier",
    "help": "AXHelp",
    "hidden": "AXHidden",
    "expanded": "AXExpanded",
    "vertical_scrollbar": "AXVerticalScrollBar",
    "horizontal_scrollbar": "AXHorizontalScrollBar",
}


class AccessibilityClient:
    def __init__(
        self, backend=None, default_max_depth: int = 12, default_max_nodes: int = 2000
    ):
        self.backend = backend
        self.default_max_depth = default_max_depth
        self.default_max_nodes = default_max_nodes
        self.locator = ElementLocator()
        self._refs: dict[str, Any] = {}
        self._elements: dict[str, UIElement] = {}

    def _backend(self):
        if self.backend is None:
            self.backend = MacOSAXBackend()
        return self.backend

    def status(self) -> dict:
        if self.backend is not None and hasattr(self.backend, "status"):
            return self.backend.status()
        return get_accessibility_status()

    def request_permission(self, prompt: bool = True) -> dict:
        return request_accessibility_permission(prompt)

    def application_tree(
        self,
        application: str | int | None = None,
        max_depth: int | None = None,
        max_nodes: int | None = None,
    ) -> UIElement:
        self._ensure_permission()
        ref, app = self._backend().application(application)
        return self._build(ref, app, (), app["name"], max_depth, max_nodes)

    def window_tree(
        self,
        application: str | int | None = None,
        window: str | None = None,
        max_depth: int | None = None,
        max_nodes: int | None = None,
    ) -> UIElement:
        self._ensure_permission()
        app_ref, app = self._backend().application(application)
        windows = (
            self._backend().copy_attribute(app_ref, ATTRIBUTES["windows"], []) or []
        )
        if not windows:
            raise ElementNotFoundError(f"No accessible windows for {app['name']}")
        selected = None
        selected_index = 0
        if window:
            for index, ref in enumerate(windows):
                if normalize_text(
                    self._backend().copy_attribute(ref, ATTRIBUTES["title"], "")
                ) == normalize_text(window):
                    selected = ref
                    selected_index = index
                    break
        else:
            selected = (
                self._backend().copy_attribute(app_ref, ATTRIBUTES["focused_window"])
                or windows[0]
            )
            selected_index = next(
                (index for index, ref in enumerate(windows) if ref == selected), 0
            )
        if selected is None:
            raise ElementNotFoundError(f"Window not found: {window}")
        title = str(
            self._backend().copy_attribute(selected, ATTRIBUTES["title"], "") or ""
        )
        return self._build(
            selected, app, (selected_index,), title, max_depth, max_nodes
        )

    def focused_element(self) -> UIElement:
        self._ensure_permission()
        backend = self._backend()
        ref = backend.copy_attribute(
            backend.system_wide(), ATTRIBUTES["focused_element"]
        )
        if ref is None:
            raise ElementNotFoundError("No focused UI element")
        _, app = backend.application(None)
        return self._build(ref, app, (), None, 0, 1)

    def find_all(
        self,
        query: ElementQuery,
        limit: int | None = None,
        max_depth: int | None = None,
        max_nodes: int | None = None,
    ) -> list[UIElementMatch]:
        root = self.application_tree(query.application, max_depth, max_nodes)
        return self.locator.find_all(root, replace(query, application=None), limit)

    def find(
        self,
        query: ElementQuery,
        max_depth: int | None = None,
        max_nodes: int | None = None,
    ) -> UIElementMatch | None:
        matches = self.find_all(query, 1, max_depth, max_nodes)
        return matches[0] if matches else None

    def get(self, identifier: str, application: str | int | None = None) -> UIElement:
        if identifier in self._elements:
            return self._elements[identifier]
        root = None
        if identifier.startswith("ax://"):
            try:
                locator_pid = int(identifier.split("/", 3)[2])
            except (IndexError, ValueError):
                locator_pid = application
            root = self.application_tree(locator_pid or application)
        elif application is not None:
            root = self.application_tree(application)
        match = (
            self.locator.find_one(root, ElementQuery(locator=identifier))
            if root
            else None
        )
        if match:
            return match.element
        raise ElementNotFoundError(f"UI element not found: {identifier}")

    def refresh(self, identifier: str) -> UIElement:
        element = self.get(identifier)
        ref = self._reference(element)
        app = {"name": element.application or "", "pid": element.application_pid or 0}
        return self._build(ref, app, element.path, element.window, 0, 1)

    def perform(self, identifier: str, action: str) -> UIElement:
        element = self.get(identifier)
        self._backend().perform_action(self._reference(element), action)
        return self.refresh(element.id)

    def set_value(self, identifier: str, value: Any) -> UIElement:
        element = self.get(identifier)
        self._backend().set_attribute(
            self._reference(element), ATTRIBUTES["value"], value
        )
        return self.refresh(element.id)

    def set_focused(self, identifier: str, focused: bool = True) -> UIElement:
        element = self.get(identifier)
        self._backend().set_attribute(
            self._reference(element), ATTRIBUTES["focused"], focused
        )
        return self.refresh(element.id)

    def set_selected(self, identifier: str, selected: bool = True) -> UIElement:
        element = self.get(identifier)
        self._backend().set_attribute(
            self._reference(element), ATTRIBUTES["selected"], selected
        )
        return self.refresh(element.id)

    def set_expanded(self, identifier: str, expanded: bool) -> UIElement:
        element = self.get(identifier)
        self._backend().set_attribute(
            self._reference(element), ATTRIBUTES["expanded"], expanded
        )
        return self.refresh(element.id)

    def scroll(self, identifier: str, direction: str, amount: float = 0.8) -> UIElement:
        element = self.get(identifier)
        backend, ref = self._backend(), self._reference(element)
        horizontal = direction in ("left", "right")
        scrollbar_attribute = (
            ATTRIBUTES["horizontal_scrollbar"]
            if horizontal
            else ATTRIBUTES["vertical_scrollbar"]
        )
        scrollbar_ref = backend.copy_attribute(ref, scrollbar_attribute)
        if scrollbar_ref is None and element.role == "AXScrollBar":
            scrollbar_ref = ref
        if scrollbar_ref is None:
            axis = "horizontal" if horizontal else "vertical"
            raise AccessibilityError(
                f"{element.role} does not expose a {axis} scroll bar"
            )
        current = backend.copy_attribute(scrollbar_ref, ATTRIBUTES["value"])
        try:
            current_value = float(current)
        except (TypeError, ValueError) as exc:
            raise AccessibilityError(
                f"Scroll bar has a non-numeric value: {current!r}"
            ) from exc
        sign = -1 if direction in ("up", "left") else 1
        new_value = min(1.0, max(0.0, current_value + sign * amount))
        backend.set_attribute(scrollbar_ref, ATTRIBUTES["value"], new_value)
        return self.refresh(element.id)

    def _ensure_permission(self):
        status = self.status()
        if status.get("supported") and not status.get("trusted"):
            raise AccessibilityPermissionError(
                status.get("instruction", "Accessibility permission denied")
            )

    def _reference(self, element: UIElement):
        ref = self._refs.get(element.id) or self._refs.get(element.locator)
        if ref is None:
            raise ElementNotFoundError(
                f"Native reference expired for {element.locator}"
            )
        return ref

    def _build(
        self,
        root_ref,
        app: dict,
        path: tuple[int, ...],
        window: str | None,
        max_depth: int | None,
        max_nodes: int | None,
    ) -> UIElement:
        limits = {"nodes": 0, "max_nodes": max_nodes or self.default_max_nodes}
        depth = self.default_max_depth if max_depth is None else max_depth
        return self._read_element(root_ref, app, path, window, depth, limits)

    def _read_element(
        self,
        ref,
        app: dict,
        path: tuple[int, ...],
        window: str | None,
        depth: int,
        limits: dict,
    ) -> UIElement:
        limits["nodes"] += 1
        backend = self._backend()

        def get(name, default=None):
            return backend.copy_attribute(ref, ATTRIBUTES[name], default)

        role = str(get("role", "AXUnknown") or "AXUnknown")
        title_value = get("title")
        title = str(title_value) if title_value is not None else None
        if role == "AXWindow" and title:
            window = title
        locator = self._make_locator(app["pid"], path, role, title)
        element_id = hashlib.sha256(locator.encode("utf-8")).hexdigest()[:20]
        element = UIElement(
            id=element_id,
            locator=locator,
            role=role,
            subrole=self._optional_string(get("subrole")),
            title=title,
            value=get("value"),
            description=self._optional_string(get("description")),
            position=backend.point(get("position")),
            size=backend.size(get("size")),
            enabled=bool(get("enabled", True)),
            focused=bool(get("focused", False)),
            selected=bool(get("selected", False)),
            actions=backend.actions(ref),
            application=app["name"],
            application_pid=app["pid"],
            window=window,
            path=path,
            attributes={
                "identifier": self._optional_string(get("identifier")),
                "help": self._optional_string(get("help")),
                "hidden": bool(get("hidden", False)),
            },
        )
        self._refs[element_id] = self._refs[locator] = ref
        self._elements[element_id] = self._elements[locator] = element
        if depth > 0 and limits["nodes"] < limits["max_nodes"]:
            children = get("children", []) or []
            for index, child_ref in enumerate(children):
                if limits["nodes"] >= limits["max_nodes"]:
                    element.attributes["truncated"] = True
                    break
                element.children.append(
                    self._read_element(
                        child_ref, app, path + (index,), window, depth - 1, limits
                    )
                )
        elif depth == 0 and (get("children", []) or []):
            element.attributes["truncated"] = True
        return element

    @staticmethod
    def _optional_string(value) -> str | None:
        return str(value) if value is not None else None

    @staticmethod
    def _make_locator(
        pid: int, path: tuple[int, ...], role: str, title: str | None
    ) -> str:
        path_value = "/".join(str(index) for index in path) or "root"
        hint = normalize_text(title or "").replace("/", "_")[:40]
        return f"ax://{pid}/{path_value}?role={role}&title={hint}"
