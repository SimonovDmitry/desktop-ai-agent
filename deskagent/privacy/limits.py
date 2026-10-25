from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Callable


class EmergencyStop:
    """Process-local kill switch checked immediately before every action."""

    def __init__(self):
        self._event = threading.Event()

    def trigger(self):
        self._event.set()

    def reset(self):
        self._event.clear()

    @property
    def triggered(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True)
class LimitDecision:
    allowed: bool
    reason: str | None = None
    code: str | None = None


class SafetyLimits:
    CLICK_TOKENS = ("click", "tap", "mouse_press")

    def __init__(self, max_clicks_per_minute=60, max_consecutive_failures=3,
                 emergency_stop: EmergencyStop | None = None, clock: Callable[[], float] = time.monotonic):
        self.max_clicks_per_minute = max_clicks_per_minute
        self.max_consecutive_failures = max_consecutive_failures
        self.emergency_stop = emergency_stop or EmergencyStop()
        self.clock = clock
        self._clicks: deque[float] = deque()
        self._failures: defaultdict[str, int] = defaultdict(int)
        self._lock = threading.RLock()

    def check(self, action_name: str, parameters: dict[str, Any]) -> LimitDecision:
        if self.emergency_stop.triggered:
            return LimitDecision(False, "Emergency stop is active", "EMERGENCY_STOP")
        key = self._key(action_name, parameters)
        with self._lock:
            if self._failures[key] >= self.max_consecutive_failures:
                return LimitDecision(False, "Repeated action failure limit reached", "REPEAT_LIMIT")
            if self._is_click(action_name):
                now = self.clock()
                while self._clicks and self._clicks[0] <= now - 60:
                    self._clicks.popleft()
                cost = self._click_cost(action_name, parameters)
                if len(self._clicks) + cost > self.max_clicks_per_minute:
                    return LimitDecision(False, "Mouse click rate limit reached", "CLICK_RATE_LIMIT")
        return LimitDecision(True)

    def record(self, action_name: str, parameters: dict[str, Any], success: bool):
        key = self._key(action_name, parameters)
        with self._lock:
            if success:
                self._failures[key] = 0
            else:
                self._failures[key] += 1
            if self._is_click(action_name):
                now = self.clock()
                self._clicks.extend([now] * self._click_cost(action_name, parameters))

    @classmethod
    def _is_click(cls, action_name: str) -> bool:
        name = action_name.casefold()
        return any(token in name for token in cls.CLICK_TOKENS)

    @staticmethod
    def _click_cost(action_name: str, parameters: dict[str, Any]) -> int:
        if "triple" in action_name:
            return 3
        if "double" in action_name:
            return 2
        return max(1, int(parameters.get("count", parameters.get("clicks", 1))))

    @staticmethod
    def _key(action_name: str, parameters: dict[str, Any]) -> str:
        return f"{action_name}:{json.dumps(parameters, sort_keys=True, default=str)}"
