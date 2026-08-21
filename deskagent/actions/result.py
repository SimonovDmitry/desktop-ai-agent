from dataclasses import dataclass
from typing import Any

@dataclass
class ActionResult:
    success: bool
    data: Any = None
    error: str | None = None
    error_code: str | None = None
    metadata: dict[str, Any] | None = None


Settings(
    log_level="INFO",
    default_volume_step=10,
    screenshot_quality=80,
    llm_model="...",
    confirmation_timeout=10,
)

@dataclass
class ActionContext:
    settings: Settings
    logger: Logger
    services: Services


@dataclass
class Services:
    system: SystemService
    display: DisplayService
    network: NetworkService
    application: ApplicationService
    window: WindowService
    clipboard: ClipboardService
    notification: NotificationService