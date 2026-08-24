import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from deskagent.core.config import Settings
from deskagent.core.context import ActionContext
from deskagent.core.services import Services, SystemServices


@pytest.fixture
def system_services():
    return SystemServices(
        audio=MagicMock(),
        clipboard=MagicMock(),
        display=MagicMock(),
        information=MagicMock(),
        mouse=MagicMock(),
        network=MagicMock(),
        notify=MagicMock(),
        power=MagicMock(),
    )


@pytest.fixture
def context(system_services):
    return ActionContext(
        settings=Settings(),
        logger=logging.getLogger("tests"),
        services=Services(system=system_services),
    )


@pytest.fixture
def action_context(context):
    return context


def assert_success(result, expected_data=None):
    assert result.success is True
    assert result.error is None
    assert result.error_code is None
    if expected_data is not None:
        assert result.data == expected_data


def assert_error(result, code):
    assert result.success is False
    assert result.error_code == code
    assert result.error
