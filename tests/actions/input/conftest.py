from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest

@pytest.fixture
def ctx():
    keyboard, mouse, clipboard, monitor, focus = [MagicMock() for _ in range(5)]
    system = SimpleNamespace(keyboard=keyboard, mouse=mouse, clipboard=clipboard,
                             input_monitor=monitor)
    return SimpleNamespace(services=SimpleNamespace(
        system=system, application=SimpleNamespace(focus=focus)))
