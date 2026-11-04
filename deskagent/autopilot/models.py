from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
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
    REPLAN = "replan"
    COMPENSATE = "compensate"


class VerificationType(str, Enum):
    CATALOG = "catalog"
    OUTPUT_EQUALS = "output_equals"
    FILE_EXISTS = "file_exists"
    ACTION = "action"


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 1
    strategy: str = "fixed"
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    max_elapsed_seconds: float | None = None
    jitter_seconds: float = 0.0
    retry_on: tuple[str, ...] = (
        "EXECUTION_ERROR",
        "TIMEOUT",
        "TEMPORARY_UNAVAILABLE",
        "VERIFICATION_FAILED",
    )

    def delay_for(self, attempt: int, random_value: float = 0.0) -> float:
        if self.strategy == "exponential":
            delay = self.initial_delay_seconds * (2 ** max(attempt - 1, 0))
        elif self.strategy == "linear":
            delay = self.initial_delay_seconds * max(attempt, 1)
        else:
            delay = self.initial_delay_seconds
        jitter = max(-1.0, min(1.0, random_value)) * self.jitter_seconds
        return max(0.0, min(delay, self.max_delay_seconds) + jitter)

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> "RetryPolicy":
        value = dict(value or {})
        if "retry_on" in value:
            value["retry_on"] = tuple(value["retry_on"])
        return cls(**value)


@dataclass(frozen=True)
class Verification:
    type: VerificationType = VerificationType.CATALOG
    arguments: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 0.0
    interval_seconds: float = 0.25

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> "Verification":
        data = dict(value or {})
        data["type"] = VerificationType(data.get("type", VerificationType.CATALOG))
        return cls(**data)


@dataclass(frozen=True)
class Compensation:
    action: str
    arguments: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = True

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> "Compensation | None":
        return cls(**value) if value else None


@dataclass
class Step:
    id: str
    title: str
    action: str
    arguments: dict[str, Any] = field(default_factory=dict)
    depends_on: tuple[str, ...] = ()
    condition: dict[str, Any] | None = None
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    timeout_seconds: float | None = None
    verifications: tuple[Verification, ...] = field(default_factory=lambda: (Verification(),))
    compensation: Compensation | None = None
    on_failure: FailurePolicy = FailurePolicy.STOP
    requires_confirmation: bool = False
    confirmation_approved: bool = False
    idempotent: bool = False
    resources: tuple[str, ...] = ("desktop_ui",)
    status: StepStatus = StepStatus.PENDING
    attempts: int = 0
    retry_at: str | None = None
    first_attempt_at: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    idempotency_key: str | None = None
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
        raw_verifications = data.pop("verification", data.get("verifications", None))
        if isinstance(raw_verifications, dict):
            raw_verifications = [raw_verifications]
        data["verifications"] = tuple(
            Verification.from_dict(item) for item in (raw_verifications or ({"type": "catalog"},))
        )
        data["compensation"] = Compensation.from_dict(data.get("compensation"))
        data["status"] = StepStatus(data.get("status", StepStatus.PENDING))
        data["on_failure"] = FailurePolicy(data.get("on_failure", FailurePolicy.STOP))
        return cls(**data)

    def definition_dict(self) -> dict[str, Any]:
        value = self.to_dict()
        for key in (
            "status", "attempts", "retry_at", "first_attempt_at", "started_at",
            "finished_at", "idempotency_key", "output", "error", "error_code",
            "confirmation_approved",
        ):
            value.pop(key, None)
        return value

    def runtime_dict(self) -> dict[str, Any]:
        return {
            key: getattr(self, key)
            for key in (
                "status", "attempts", "retry_at", "first_attempt_at", "started_at",
                "finished_at", "idempotency_key", "output", "error", "error_code",
                "confirmation_approved",
            )
        }


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

    def definition_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "metadata": self.metadata,
            "steps": [step.definition_dict() for step in self.steps],
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
    action_count: int = 0
    replan_count: int = 0
    max_replans: int = 3
    max_duration_seconds: float = 3600.0
    started_at: str | None = None
    approved_plan_hash: str | None = None
    dry_run: bool = False
    owner_id: str | None = None
    lease_expires_at: str | None = None
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
            "action_count": self.action_count,
            "replan_count": self.replan_count,
            "max_replans": self.max_replans,
            "max_duration_seconds": self.max_duration_seconds,
            "started_at": self.started_at,
            "approved_plan_hash": self.approved_plan_hash,
            "dry_run": self.dry_run,
            "owner_id": self.owner_id,
            "lease_expires_at": self.lease_expires_at,
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
            action_count=int(value.get("action_count", 0)),
            replan_count=int(value.get("replan_count", 0)),
            max_replans=int(value.get("max_replans", 3)),
            max_duration_seconds=float(value.get("max_duration_seconds", 3600.0)),
            started_at=value.get("started_at"),
            approved_plan_hash=value.get("approved_plan_hash"),
            dry_run=bool(value.get("dry_run", False)),
            owner_id=value.get("owner_id"),
            lease_expires_at=value.get("lease_expires_at"),
            created_at=value["created_at"],
            updated_at=value["updated_at"],
        )

    def deadline(self) -> datetime | None:
        if not self.started_at or not self.max_duration_seconds:
            return None
        return datetime.fromisoformat(self.started_at) + timedelta(seconds=self.max_duration_seconds)
