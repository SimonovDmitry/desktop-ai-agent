import platform

import pytest

from deskagent.core.services import MacOSSystemServices, Services, ServicesFactory


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS integration test")
def test_real_services_factory_builds_macos_services():
    services = ServicesFactory.create()
    assert isinstance(services, Services)
    assert isinstance(services.system, MacOSSystemServices)
    assert services.system.audio is not None
    assert services.system.network is not None
