import logging
from unittest.mock import MagicMock

from deskagent.core.config import Settings
from deskagent.core.context import ActionContext
from deskagent.core.services import Services, SystemServices


def test_action_context_stores_dependencies():
    system = SystemServices(
        audio=MagicMock(),
        clipboard=MagicMock(),
        display=MagicMock(),
        information=MagicMock(),
        mouse=MagicMock(),
        network=MagicMock(),
        notify=MagicMock(),
        power=MagicMock(),
    )
    services = Services(system=system)
    logger = logging.getLogger("context-test")
    settings = Settings()

    context = ActionContext(settings=settings, logger=logger, services=services)

    assert context.settings is settings
    assert context.logger is logger
    assert context.services is services
    assert context.services.system is system
