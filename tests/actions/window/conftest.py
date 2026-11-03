from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def window_context():
    return SimpleNamespace(services=SimpleNamespace(window=MagicMock()))


def assert_success(result, expected_data=None):
    assert result.success is True
    assert result.error is None
    assert result.error_code is None
    if expected_data is not None:
        assert result.data == expected_data


def assert_system_error(result, message=None):
    assert result.success is False
    assert result.error_code == "SYSTEM_ERROR"
    if message is not None:
        assert result.error == message
