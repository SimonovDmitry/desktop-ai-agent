from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def window_context():
    return SimpleNamespace(services=SimpleNamespace(window=MagicMock()))
