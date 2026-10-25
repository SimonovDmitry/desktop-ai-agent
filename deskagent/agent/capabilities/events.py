from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass(frozen=True)
class AgentEvent:
    type: str
    data: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())


class EventBus:
    def __init__(self):
        self.handlers = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable):
        self.handlers[event_type].append(handler)

    def publish(self, event: AgentEvent):
        for handler in [*self.handlers[event.type], *self.handlers["*"]]:
            handler(event)


class ProactiveRules:
    DISTRACTIONS = {"youtube", "instagram", "tiktok", "vk", "reddit", "telegram"}

    def evaluate(self, screen: dict, system: dict, focus_mode=False):
        events = []
        battery = system.get("battery") or {}
        if battery.get("percentage", 100) <= 10 and not battery.get("charging"):
            events.append(AgentEvent("low_battery", battery))
        app = str(screen.get("application", "")).lower()
        if focus_mode and any(name in app for name in self.DISTRACTIONS):
            events.append(AgentEvent("procrastination", {"application": screen.get("application")}))
        return events
