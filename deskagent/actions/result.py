from dataclasses import dataclass
from typing import Any

@dataclass
class ActionResult:
    success: bool
    data: Any = None
    error: str | None = None
    error_code: str | None = None
    metadata: dict[str, Any] | None = None
