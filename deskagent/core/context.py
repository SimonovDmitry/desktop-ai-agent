import logging
from dataclasses import dataclass

from deskagent.core.config import Settings
from deskagent.core.services import Services

@dataclass
class ActionContext:
    settings: Settings
    logger: logging.Logger
    services: Services
