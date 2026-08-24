from enum import Enum


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