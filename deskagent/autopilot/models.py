from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class SessionStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    WAITING_FOR_USER = "waiting_for_user"
    PAUSED = "paused"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"
    FAILED = "failed"
    COMPLETED = "completed"
    RECOVERING = "recovering"


class StepStatus(str, Enum):
    PENDING = "pending"
    BLOCKED = "blocked"
    READY = "ready"
    RUNNING = "running"
    VERIFYING = "verifying"
    RETRY_SCHEDULED = "retry_scheduled"
    WAITING_FOR_USER = "waiting_for_user"
    SUCCEEDED = "succeeded"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AutopilotMode(str, Enum):
    MANUAL = "manual"
    GUIDED = "guided"
    AUTOPILOT = "autopilot"


class FailurePolicy(str, Enum):
    STOP = "stop"
    SKIP = "skip"


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1
    strategy: str = "fixed"
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    retry_on: tuple[str, ...] = (
        "EXECUTION_ERROR",
        "TIMEOUT",
        "TEMPORARY_UNAVAILABLE",
        "VERIFICATION_FAILED",
    )

    def delay_for(self, attempt: int) -> float:
        if self.strategy == "exponential":
            delay = self.initial_delay_seconds * (2 ** max(attempt - 1, 0))
        elif self.strategy == "linear":
            delay = self.initial_delay_seconds * max(attempt, 1)
        else:
            delay = self.initial_delay_seconds
        return min(delay, self.max_delay_seconds)

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> "RetryPolicy":
        value = dict(value or {})
        if "retry_on" in value:
            value["retry_on"] = tuple(value["retry_on"])
        return cls(**value)


@dataclass
class Step:
    id: str
    title: str
    action: str
    arguments: dict[str, Any] = field(default_factory=dict)
    depends_on: tuple[str, ...] = ()
    condition: dict[str, Any] | None = None
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    on_failure: FailurePolicy = FailurePolicy.STOP
    requires_confirmation: bool = False
    confirmation_approved: bool = False
    idempotent: bool = False
    resources: tuple[str, ...] = ("desktop_ui",)
    status: StepStatus = StepStatus.PENDING
    attempts: int = 0
    output: Any = None
    error: str | None = None
    error_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["on_failure"] = self.on_failure.value
        return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Step":
        data = dict(value)
        data["depends_on"] = tuple(data.get("depends_on", ()))
        data["resources"] = tuple(data.get("resources", ("desktop_ui",)))
        data["retry"] = RetryPolicy.from_dict(data.get("retry"))
        data["status"] = StepStatus(data.get("status", StepStatus.PENDING))
        data["on_failure"] = FailurePolicy(data.get("on_failure", FailurePolicy.STOP))
        return cls(**data)


@dataclass
class Plan:
    steps: list[Step]
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "metadata": self.metadata,
            "steps": [step.to_dict() for step in self.steps],
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Plan":
        return cls(
            [Step.from_dict(item) for item in value.get("steps", [])],
            int(value.get("version", 1)),
            dict(value.get("metadata", {})),
        )

    def step(self, step_id: str) -> Step:
        for item in self.steps:
            if item.id == step_id:
                return item
        raise KeyError(step_id)


@dataclass
class Session:
    goal: str
    plan: Plan
    id: str = field(default_factory=lambda: f"session_{uuid.uuid4().hex}")
    status: SessionStatus = SessionStatus.DRAFT
    mode: AutopilotMode = AutopilotMode.GUIDED
    current_step_id: str | None = None
    pending_confirmation: dict[str, Any] | None = None
    error: str | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "plan": self.plan.to_dict(),
            "status": self.status.value,
            "mode": self.mode.value,
            "current_step_id": self.current_step_id,
            "pending_confirmation": self.pending_confirmation,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Session":
        return cls(
            id=value["id"],
            goal=value["goal"],
            plan=Plan.from_dict(value["plan"]),
            status=SessionStatus(value["status"]),
            mode=AutopilotMode(value.get("mode", AutopilotMode.GUIDED)),
            current_step_id=value.get("current_step_id"),
            pending_confirmation=value.get("pending_confirmation"),
            error=value.get("error"),
            created_at=value["created_at"],
            updated_at=value["updated_at"],
        )
