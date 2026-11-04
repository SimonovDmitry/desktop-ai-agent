from __future__ import annotations

import threading
import time
from collections.abc import Callable

from deskagent.perception.accessibility.models import (
    ElementQuery,
    UIElement,
    UIElementMatch,
)


class AccessibilityObserver:
    """Cancellation-aware polling for asynchronous GUI state changes."""

    def __init__(
        self,
        client,
        poll_interval: float = 0.2,
        clock=time.monotonic,
        sleeper=time.sleep,
    ):
        self.client = client
        self.poll_interval = poll_interval
        self.clock = clock
        self.sleeper = sleeper
        self._cancelled = threading.Event()

    def cancel(self):
        self._cancelled.set()

    def reset(self):
        self._cancelled.clear()

    def wait_for(
        self, predicate: Callable[[], object], timeout: float, description: str
    ):
        deadline = self.clock() + timeout
        last_error = None
        while True:
            if self._cancelled.is_set():
                raise InterruptedError(f"Cancelled while waiting for {description}")
            try:
                result = predicate()
                if result:
                    return result
            except Exception as exc:
                last_error = exc
            remaining = deadline - self.clock()
            if remaining <= 0:
                break
            self.sleeper(min(self.poll_interval, remaining))
        suffix = f": {last_error}" if last_error else ""
        raise TimeoutError(
            f"Timed out after {timeout:g}s waiting for {description}{suffix}"
        )

    def element(self, query: ElementQuery, timeout: float = 10) -> UIElementMatch:
        return self.wait_for(lambda: self.client.find(query), timeout, "UI element")

    def disappearance(self, query: ElementQuery, timeout: float = 10) -> bool:
        def missing():
            return self.client.find(query) is None

        return bool(self.wait_for(missing, timeout, "UI element to disappear"))

    def state(
        self,
        identifier: str,
        predicate: Callable[[UIElement], bool],
        timeout: float = 10,
        description: str = "UI element state",
    ) -> UIElement:
        def matches():
            element = self.client.refresh(identifier)
            return element if predicate(element) else None

        return self.wait_for(matches, timeout, description)
