from dataclasses import dataclass
from enum import Enum
from typing import Any


class RiskLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionCategory(Enum):
    SYSTEM = "system"
    APPLICATION = "application"
    WINDOW = "window"
    INPUT = "input"
    FILE = "file"


@dataclass
class ActionResult:
    success: bool
    data: Any = None
    error: str | None = None
    error_code: str | None = None
    metadata: dict[str, Any] | None = None
