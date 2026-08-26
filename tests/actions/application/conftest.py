import logging

import pytest
from unittest.mock import MagicMock

from deskagent.core.config import Settings
from deskagent.core.context import ActionContext
# TODO добавить в platform реализацию application и привести тесты в нормальный вид и
#  все переходить к сл модулю

@pytest.fixture
def application_context():
    services = MagicMock()
    services.application = MagicMock()

    return ActionContext(
        settings=Settings(),
        logger=logging.getLogger("application-actions-test"),
        services=services,
    )


def assert_success(result, data=None):
    assert result.success is True
    assert result.error is None
    assert result.error_code is None
    if data is not None:
        assert result.data == data


def assert_error(result, error_code):
    assert result.success is False
    assert result.error_code == error_code
    assert result.error is not None
