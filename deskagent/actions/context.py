from dataclasses import dataclass


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