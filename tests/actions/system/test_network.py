import pytest

from deskagent.actions.system.network import (
    CheckInternetConnection,
    GetDefaultGateway,
    GetDNS,
    GetHostname,
    GetIPAddress,
    GetNetworkInterfaces,
    GetNetworkStatus,
    GetPublicIPAddress,
    PingHost,
)
from tests.conftest import assert_error, assert_success


def test_get_network_status_success(context):
    data = {"connected": True, "connection_type": "wifi", "interface": "en0"}
    context.services.system.network.get_network_status.return_value = data
    result = GetNetworkStatus().execute(context, {})
    assert_success(result, data)


def test_get_ip_address_without_interface(context):
    data = {"addresses": [{"interface": "en0", "address": "192.168.1.2", "version": 4}]}
    context.services.system.network.get_ip_address.return_value = data
    result = GetIPAddress().execute(context, {})
    assert_success(result, data)
    context.services.system.network.get_ip_address.assert_called_once_with(None)


def test_get_ip_address_with_interface(context):
    data = {"interface": "en0", "addresses": []}
    context.services.system.network.get_ip_address.return_value = data
    result = GetIPAddress().execute(context, {"interface": "en0"})
    assert_success(result, data)
    context.services.system.network.get_ip_address.assert_called_once_with("en0")


@pytest.mark.parametrize(
    ("action_class", "method", "return_value"),
    [
        (GetHostname, "get_hostname", {"hostname": "host", "fqdn": "host.local"}),
        (GetNetworkInterfaces, "get_network_interfaces", [{"name": "en0"}]),
        (GetPublicIPAddress, "get_public_ip_address", "203.0.113.10"),
        (GetDefaultGateway, "get_default_gateway", "192.168.1.1"),
        (GetDNS, "get_dns", ["1.1.1.1"]),
    ],
)
def test_network_information_success(context, action_class, method, return_value):
    getattr(context.services.system.network, method).return_value = return_value
    result = action_class().execute(context, {})
    assert result.success is True
    getattr(context.services.system.network, method).assert_called_once_with()


def test_ping_host_requires_host(context):
    result = PingHost().execute(context, {})
    assert_error(result, "MISSING_PARAM")


def test_ping_host_success(context):
    data = {"reachable": True, "latency_ms": 10.2}
    context.services.system.network.ping_host.return_value = data
    result = PingHost().execute(context, {"host": "example.com"})
    assert_success(result, data)
    context.services.system.network.ping_host.assert_called_once_with("example.com")


def test_ping_host_system_error(context):
    context.services.system.network.ping_host.side_effect = RuntimeError("ping failed")
    result = PingHost().execute(context, {"host": "example.com"})
    assert_error(result, "SYSTEM_ERROR")


def test_check_internet_connection_success(context):
    result = CheckInternetConnection().execute(context, {})
    context.services.system.network.check_internet_connection.assert_called_once_with()
    assert_success(result, {"internet_accessible": context.services.system.network.check_internet_connection.return_value})


@pytest.mark.parametrize(
    "action_class",
    [
        GetNetworkStatus,
        GetIPAddress,
        GetHostname,
        GetNetworkInterfaces,
        GetPublicIPAddress,
        GetDefaultGateway,
        GetDNS,
        CheckInternetConnection,
    ],
)
def test_network_actions_convert_service_exceptions_to_action_result(context, action_class):
    method_map = {
        GetNetworkStatus: "get_network_status",
        GetIPAddress: "get_ip_address",
        GetHostname: "get_hostname",
        GetNetworkInterfaces: "get_network_interfaces",
        GetPublicIPAddress: "get_public_ip_address",
        GetDefaultGateway: "get_default_gateway",
        GetDNS: "get_dns",
        CheckInternetConnection: "check_internet_connection",
    }
    getattr(context.services.system.network, method_map[action_class]).side_effect = RuntimeError("network failed")
    result = action_class().execute(context, {})
    assert_error(result, "SYSTEM_ERROR")
