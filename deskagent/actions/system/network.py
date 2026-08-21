from deskagent.actions.base import Action
from deskagent.actions.result import ActionResult
from deskagent.actions.context import ActionContext
from deskagent.actions.types import RiskLevel, ActionCategory


#TODO проверить работоспособность GetNetworkStatus GetIPAddress GetHostname GetNetworkInterfaces
class GetNetworkStatus(Action):
    name = "get_network_status"
    description = "Get the overall network connectivity status (WiFi, Ethernet, VPN)"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            status = context.services.system.network.get_network_status()
            return ActionResult(success=True, data=status)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetIPAddress(Action):
    name = "get_ip_address"
    description = "Get local IP addresses for a specific interface or all active ones"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context, interface=None):
        try:
            ips = context.services.system.network.get_ip_address(interface)
            return ActionResult(success=True, data=ips)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetHostname(Action):
    name = "get_hostname"
    description = "Get the computer's network hostname and FQDN"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            hostname_info = context.services.system.network.get_hostname()
            return ActionResult(success=True, data=hostname_info)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


class GetNetworkInterfaces(Action):
    name = "get_network_interfaces"
    description = "Get detailed information about all network interfaces"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            interfaces = context.services.system.network.get_network_interfaces()
            return ActionResult(success=True, data={"interfaces": interfaces})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать получение публичного IP (через внешний API)
class GetPublicIPAddress(Action):
    name = "get_public_ip_address"
    description = "Get the public IP address using an external service"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            public_ip = context.services.system.network.get_public_ip_address()
            return ActionResult(success=True, data={"public_ip": public_ip})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать получение шлюза по умолчанию
class GetDefaultGateway(Action):
    name = "get_default_gateway"
    description = "Get the default network gateway"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            gateway = context.services.system.network.get_default_gateway()
            return ActionResult(success=True, data={"gateway": gateway})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать получение настроек DNS
class GetDNS(Action):
    name = "get_dns"
    description = "Get the current DNS server settings"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            dns_settings = context.services.system.network.get_dns()
            return ActionResult(success=True, data={"dns": dns_settings})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать утилиту Ping
class PingHost(Action):
    name = "ping_host"
    description = "Ping a remote host to check availability and latency"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context, host):
        try:
            ping_res = context.services.system.network.ping_host(host)
            return ActionResult(success=True, data=ping_res)

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")


# TODO: Реализовать проверку интернет-соединения
class CheckInternetConnection(Action):
    name = "check_internet_connection"
    description = "Check if the computer has an active internet connection"
    category = ActionCategory.SYSTEM
    risk_level = RiskLevel.LOW
    requires_confirmation = False
    reversible = False

    def execute(self, context):
        try:
            is_connected = context.services.system.network.check_internet_connection()
            return ActionResult(success=True, data={"internet_accessible": is_connected})

        except Exception as exc:
            return ActionResult(success=False, error=str(exc), error_code="SYSTEM_ERROR")