from unittest.mock import MagicMock

import pytest

from deskagent.core.services import MacOSSystemServices, Services, ServicesFactory, SystemServices


def test_system_services_stores_all_system_services():
    values = {
        "audio": MagicMock(),
        "clipboard": MagicMock(),
        "display": MagicMock(),
        "information": MagicMock(),
        "mouse": MagicMock(),
        "network": MagicMock(),
        "notify": MagicMock(),
        "power": MagicMock(),
    }
    services = SystemServices(**values)

    for name, value in values.items():
        assert getattr(services, name) is value


def test_services_stores_system_services():
    system = MagicMock(spec=SystemServices)
    services = Services(system=system)
    assert services.system is system


def test_factory_returns_macos_for_darwin(monkeypatch):
    monkeypatch.setattr("deskagent.core.services.platform.system", lambda: "Darwin")
    assert ServicesFactory.get_platform() == "macos"


def test_factory_returns_windows_for_windows(monkeypatch):
    monkeypatch.setattr("deskagent.core.services.platform.system", lambda: "Windows")
    assert ServicesFactory.get_platform() == "windows"


def test_factory_rejects_unsupported_platform(monkeypatch):
    monkeypatch.setattr("deskagent.core.services.platform.system", lambda: "Linux")
    with pytest.raises(RuntimeError, match="Unsupported platform"):
        ServicesFactory.get_platform()


def test_macos_system_services_creates_expected_service_types():
    services = MacOSSystemServices()
    assert services.audio is not None
    assert services.clipboard is not None
    assert services.display is not None
    assert services.information is not None
    assert services.mouse is not None
    assert services.network is not None
    assert services.notify is not None
    assert services.power is not None


def test_factory_create_macos(monkeypatch):
    monkeypatch.setattr("deskagent.core.services.ServicesFactory.get_platform", lambda: "macos")
    services = ServicesFactory.create()
    assert isinstance(services, Services)
    assert isinstance(services.system, MacOSSystemServices)


def test_factory_create_unknown_platform_raises(monkeypatch):
    monkeypatch.setattr("deskagent.core.services.ServicesFactory.get_platform", lambda: "linux")
    with pytest.raises(RuntimeError, match="Unsupported platform"):
        ServicesFactory.create()
